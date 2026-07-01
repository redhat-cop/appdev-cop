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
| Bucket | `models` | `AWS_S3_BUCKET` (OpenShift AI env / S3 connection) |
| Prefix | `finetuned/custom/v1/` | `S3_PREFIX` |
| Local model path | `./granite-fine-tuned-checkpoints` | `LOCAL_MODEL_PATH` |
| Endpoint | (required for upload) | `AWS_S3_ENDPOINT` |
| Credentials | (required for upload) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |
| Skip upload | upload enabled | `UPLOAD_TO_S3=false` |

To use a different bucket, either create that bucket in MinIO or set the variables in OpenShift AI — you do not need to edit the script.

## Configure S3 on OpenShift AI (before running)

Set these in your **OpenShift AI Workbench** project (environment variables or S3 connection), not via shell `export`:

| Variable | Value |
|----------|-------|
| `AWS_S3_ENDPOINT` | MinIO route URL (e.g. `https://<minio-route>`) |
| `AWS_ACCESS_KEY_ID` | MinIO access key (from Helm values: `minioadmin`) |
| `AWS_SECRET_ACCESS_KEY` | MinIO secret key (from Helm values) |
| `AWS_S3_BUCKET` | `models` |
| `S3_PREFIX` | `finetuned/custom/v1/` |
| `LOCAL_MODEL_PATH` | `./granite-fine-tuned-checkpoints` (optional) |
| `UPLOAD_TO_S3` | `true` (optional; set `false` to skip upload) |

**Recommended:** create an **S3 connection** in OpenShift AI Workbench — it maps access key, secret key, endpoint, and bucket into the environment for your notebook/session.

Credentials match `openshift/helm/minio-ocp/minio-ocp-values.yaml` unless you changed them at install time.

## Run the script

From the `fine-tuning` folder:

```bash
cd knowledge-base-ai-assistant/fine-tuning
python fine_tune_model.py
```

### From Jupyter (OpenShift AI Workbench)

Use the companion notebook:

```text
fine-tuning/run_fine_tune_model.ipynb
```

Configure the **S3 connection** in OpenShift AI first (see above), then run:

```python
%cd knowledge-base-ai-assistant/fine-tuning
%run fine_tune_model.py
```

## Outputs

| Location | Content |
|----------|---------|
| `./granite-fine-tuned-checkpoints/` | Local fine-tuned model + tokenizer + `training_metadata.json` |
| `s3://models/finetuned/custom/v1/` | **Full artifact directory** uploaded for inner-loop input |

Uploaded to S3 (all files from the local output directory):

- `config.json`
- Model weights (`model.safetensors` or `pytorch_model.bin`)
- Tokenizer files (`tokenizer_config.json`, etc.)
- `training_metadata.json`

The script validates these exist locally before upload.

## Next step

Compile and run the inner-loop Kubeflow pipeline from the workbench:

```python
!python pipelines/inner_loop/inner_loop_pipeline.py
```

Then upload `inner_loop_pipeline.yaml` in the Kubeflow Pipelines UI (or submit with the KFP client). It references `s3://models/finetuned/custom/v1/` as the starting model path.
