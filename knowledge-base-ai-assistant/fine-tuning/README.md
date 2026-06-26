# Fine-tuning

Supervised fine-tuning (SFT) of **Granite 8B** on synthetic data produced by the SDG step, then upload of the native PyTorch artifact to S3/MinIO for the inner-loop pipeline.

## Pipeline position

```text
sdg/sdg_flow.py  →  synthetic_training_data.jsonl
fine-tuning/fine_tune_model.py  →  s3://models/finetuned/custom/v1/
pipelines/inner_loop/
```

## Prerequisites

1. **SDG complete** — `synthetic_training_data.jsonl` must exist (default path in script: `sdg_hub/synthetic_training_data.jsonl` on the workbench).
2. **Base model cached locally** — `ibm-granite/granite-3.0-8b-instruct` (script runs in offline Hugging Face mode).
3. **GPU** — ~24 GB VRAM recommended (e.g. L4) for Granite 8B in bf16.
4. **S3 / MinIO** — bucket and credentials for upload after training.

### Python packages

Install on OpenShift AI Workbench (or your venv) if not already present:

```bash
pip install torch transformers datasets boto3
```

The workbench image may include some of these; install any missing imports before running.

### S3 / MinIO on OpenShift

Install MinIO using the Helm chart in this repo:

```text
openshift/helm/minio-ocp/
```

Example install/upgrade:

```bash
helm upgrade my-minio ./openshift/helm/minio-ocp \
  -f ./openshift/helm/minio-ocp/minio-ocp-values.yaml \
  -n open-s3-minio
```

Create an S3 bucket named **`models`** in the MinIO console (or use your own bucket name — see below).

Default upload target in `fine_tune_model.py`:

```text
s3://models/finetuned/custom/v1/
```

| Setting | Default | Override |
|---------|---------|----------|
| Bucket | `models` | `S3_BUCKET` env var |
| Prefix | `finetuned/custom/v1/` | `S3_PREFIX` env var |
| Endpoint | (none) | `S3_ENDPOINT_URL` — set to your MinIO route on OCP |
| Credentials | — | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (MinIO root user/password from Helm values) |
| Skip upload | upload enabled | `UPLOAD_TO_S3=false` |

To use a different bucket, either create that bucket in MinIO or change the env vars before running — you do not need to edit the script.

## Configure S3 (before running)

```bash
export S3_BUCKET="models"
export S3_PREFIX="finetuned/custom/v1/"
export S3_ENDPOINT_URL="https://<minio-route>"
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minio-strong-password"
export UPLOAD_TO_S3="true"
```

Credentials match `openshift/helm/minio-ocp/minio-ocp-values.yaml` unless you changed them at install time.

## Run the script

From the `fine-tuning` folder:

```bash
cd knowledge-base-ai-assistant/fine-tuning
python fine_tune_model.py
```

### From Jupyter (OpenShift AI Workbench)

Use the companion notebook for step-by-step explanation:

```text
fine-tuning/run_fine_tune_model.ipynb
```

Or run directly:

```python
%cd knowledge-base-ai-assistant/fine-tuning
# set os.environ[...] for S3 first
%run fine_tune_model.py
```

## Outputs

| Location | Content |
|----------|---------|
| `./granite-fine-tuned-checkpoints/` | Local fine-tuned model + tokenizer + `training_metadata.json` |
| `s3://models/finetuned/custom/v1/` | Same artifact uploaded for inner-loop pipeline input |

## Next step

Run the inner-loop Kubeflow pipeline:

```text
pipelines/inner_loop/run_inner_loop_pipeline.ipynb
```

It references `s3://models/finetuned/custom/v1/` as the starting model path.
