import boto3
s3 = boto3.client('s3', endpoint_url="http://my-minio.open-s3-minio.svc.cluster.local:9000", verify=False)
print(s3.list_buckets())
