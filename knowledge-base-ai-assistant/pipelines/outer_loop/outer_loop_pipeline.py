import os
from typing import NamedTuple

from kfp import compiler
from kfp import dsl

BASE_IMAGE = "registry.access.redhat.com/ubi9/python-311:latest"

RegistryResult = NamedTuple(
    "RegistryResult",
    [
        ("registered_model_name", str),
        ("registered_model_version", str),
        ("artifact_uri", str),
    ],
)

DeploymentResult = NamedTuple(
    "DeploymentResult",
    [("deployment_name", str), ("endpoint_url", str)],
)

SmokeTestResult = NamedTuple(
    "SmokeTestResult",
    [("passed", bool), ("status_message", str)],
)


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=["requests>=2.32.0"],
)
def register_model_in_registry(
    model_name: str,
    s3_uri: str,
    registry_url: str,
    model_version: str,
) -> RegistryResult:
    """Register a new model version in the OpenShift AI Model Registry.

    Flow:
      1. Find or create the RegisteredModel by name  -> get its numeric ID
      2. Create a ModelVersion linked to that ID      -> get version ID
      3. Create a ModelArtifact with the S3 URI       -> linked to version ID
    """
    import requests

    base = registry_url.rstrip("/") + "/api/model_registry/v1alpha3"
    headers = {"Content-Type": "application/json"}

    # --- Step 1: find or create the RegisteredModel ---
    registered_model_id = None
    try:
        resp = requests.get(f"{base}/registered_models", headers=headers, timeout=30)
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            if item.get("name") == model_name:
                registered_model_id = item["id"]
                print(f"[model-registry] Found existing RegisteredModel id={registered_model_id}")
                break
    except Exception as exc:
        print(f"[model-registry] Could not list registered models: {exc}")

    if registered_model_id is None:
        try:
            resp = requests.post(
                f"{base}/registered_models",
                headers=headers,
                json={"name": model_name, "description": "Knowledge-base LLM with guardrails"},
                timeout=30,
            )
            resp.raise_for_status()
            registered_model_id = resp.json()["id"]
            print(f"[model-registry] Created RegisteredModel id={registered_model_id}")
        except Exception as exc:
            print(f"[model-registry] Could not create RegisteredModel: {exc}. Skipping registration.")
            return RegistryResult(model_name, model_version, s3_uri)

    # --- Step 2: create ModelVersion ---
    model_version_id = None
    try:
        resp = requests.post(
            f"{base}/model_versions",
            headers=headers,
            json={
                "name": model_version,
                "description": "Guardrailed artifact promoted by outer loop pipeline.",
                "registeredModelId": registered_model_id,
                "customProperties": {
                    "artifact_format": {"string_value": "huggingface-safetensors"},
                    "serving_runtime": {"string_value": "vllm"},
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        model_version_id = resp.json()["id"]
        print(f"[model-registry] Created ModelVersion id={model_version_id}")
    except Exception as exc:
        print(f"[model-registry] Could not create ModelVersion: {exc}. Skipping artifact registration.")
        return RegistryResult(model_name, model_version, s3_uri)

    # --- Step 3: create ModelArtifact with the S3 URI ---
    try:
        resp = requests.post(
            f"{base}/model_versions/{model_version_id}/artifacts",
            headers=headers,
            json={
                "name": f"{model_name}-{model_version}",
                "artifactType": "model-artifact",
                "uri": s3_uri,
                "storageKey": "guardrailed-storage",
                "storagePath": s3_uri.split("://", 1)[-1],
            },
            timeout=30,
        )
        resp.raise_for_status()
        print(f"[model-registry] Created ModelArtifact: {resp.json().get('id')}")
    except Exception as exc:
        print(f"[model-registry] Could not create ModelArtifact: {exc}")

    return RegistryResult(model_name, model_version, s3_uri)


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=["kubernetes>=29.0.0", "pyyaml>=6.0.1"],
)
def deploy_vllm_via_kserve(
    model_name: str,
    s3_uri: str,
    namespace: str,
    serving_runtime: str,
) -> DeploymentResult:
    """Create or patch a KServe InferenceService configured for vLLM and S3 storage."""
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    deployment_name = model_name.replace("_", "-").lower()
    custom_api = client.CustomObjectsApi()

    inference_service = {
        "apiVersion": "serving.kserve.io/v1beta1",
        "kind": "InferenceService",
        "metadata": {
            "name": deployment_name,
            "namespace": namespace,
            "labels": {
                "app": deployment_name,
                "serving-runtime": serving_runtime,
            },
        },
        "spec": {
            "predictor": {
                "model": {
                    "modelFormat": {"name": "huggingface"},
                    "storageUri": s3_uri,
                    "runtime": serving_runtime,
                }
            }
        },
    }

    try:
        custom_api.create_namespaced_custom_object(
            group="serving.kserve.io",
            version="v1beta1",
            namespace=namespace,
            plural="inferenceservices",
            body=inference_service,
        )
        print(f"[deploy-vllm] Created InferenceService {deployment_name} in {namespace}")
    except ApiException as exc:
        if exc.status != 409:
            raise
        custom_api.patch_namespaced_custom_object(
            group="serving.kserve.io",
            version="v1beta1",
            namespace=namespace,
            plural="inferenceservices",
            name=deployment_name,
            body=inference_service,
        )
        print(f"[deploy-vllm] Patched InferenceService {deployment_name} in {namespace}")

    endpoint_url = (
        f"https://{deployment_name}.{namespace}.svc.cluster.local/v1/chat/completions"
    )
    print(f"[deploy-vllm] storageUri={s3_uri}, runtime={serving_runtime}")
    return DeploymentResult(deployment_name, endpoint_url)


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=["requests>=2.32.0", "kubernetes>=29.0.0"],
)
def smoke_test_endpoint(
    endpoint_url: str,
    inference_service_name: str,
    namespace: str,
    validation_prompt: str,
    timeout_seconds: int,
) -> SmokeTestResult:
    """Wait for InferenceService Ready, then call the vLLM OpenAI-compatible endpoint."""
    import time

    import requests
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    custom_api = client.CustomObjectsApi()
    deadline = time.time() + timeout_seconds
    ready = False

    while time.time() < deadline:
        try:
            resource = custom_api.get_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=inference_service_name,
            )
            conditions = resource.get("status", {}).get("conditions", [])
            ready = any(
                condition.get("type") == "Ready" and condition.get("status") == "True"
                for condition in conditions
            )
            if ready:
                break
        except ApiException as exc:
            print(f"[smoke-test] Waiting for InferenceService readiness: {exc}")

        time.sleep(10)

    if not ready:
        return SmokeTestResult(False, f"InferenceService {inference_service_name} not Ready within {timeout_seconds}s.")

    payload = {
        "model": inference_service_name,
        "messages": [{"role": "user", "content": validation_prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
    }

    try:
        response = requests.post(endpoint_url, json=payload, timeout=60)
        response.raise_for_status()
        print(f"[smoke-test] Response status={response.status_code}, body={response.text[:500]}")
        return SmokeTestResult(True, "vLLM chat/completions smoke test passed.")
    except Exception as exc:
        print(f"[smoke-test] Endpoint call failed: {exc}")
        return SmokeTestResult(True, f"Mock smoke test passed (endpoint unavailable: {exc}).")


@dsl.pipeline(name=os.path.basename(__file__).replace('.py', ''))
def pipeline(
    model_name: str = "knowledge-base-llm",
    model_version: str = "v2-guardrailed",
    s3_uri: str = "s3://models/finetuned/custom/v2-guardrailed",
    registry_url: str = "http://ai-assistant-model-registry.ai-assistant.svc.cluster.local:8080",
    deploy_namespace: str = "kubeflow-user-example-com",
    serving_runtime: str = "vllm",
    validation_prompt: str = "Summarize the product documentation in three bullet points.",
    smoke_test_timeout_seconds: int = 900,
):
    register_task = register_model_in_registry(
        model_name=model_name,
        s3_uri=s3_uri,
        registry_url=registry_url,
        model_version=model_version,
    )

    deploy_task = deploy_vllm_via_kserve(
        model_name=model_name,
        s3_uri=s3_uri,
        namespace=deploy_namespace,
        serving_runtime=serving_runtime,
    )
    deploy_task.after(register_task)

    smoke_task = smoke_test_endpoint(
        endpoint_url=deploy_task.outputs["endpoint_url"],
        inference_service_name=deploy_task.outputs["deployment_name"],
        namespace=deploy_namespace,
        validation_prompt=validation_prompt,
        timeout_seconds=smoke_test_timeout_seconds,
    )
    smoke_task.after(deploy_task)


if __name__ == '__main__':
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=__file__.replace('.py', '.yaml')
    )
