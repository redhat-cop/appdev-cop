
# Data Grid on OCP Demo

This project demonstrates some core functionality of Red Hat Data Grid in OpenShift. 

## Overview

### Scope

The following features are explored in this application:

- Server Configuration
  - Creating new caches
  - Enabling RBAC / security
  - Enabling TLS for external cluster traffic
  - Deploying custom code
  - Configuring custom cache loaders
- Cache functionality
  - Connecting to the RHDG cluster, from within OCP and externally
  - Basic cache operations (gets and puts)
  - Executing remote tasks
- Cluster management
  - Node discovery and clustering
  - Starting and stopping RHDG nodes
  - Scaling the cluster
  - Cross-Site replication (Operator only)

### Design

This demo consists of three parts:
- RHDG server code, made available to RHDG via an HTTPD node
- An RHDG cluster
  - Configurations for setting up the cluster via both the RHDG Operator and Helm are provided
- A simple Spring Boot client application that interacts with the RHDG cluster

## Running the demo

### Prerequisites

- Access to an OpenShift cluster. For local testing, [OpenShift Local](https://developers.redhat.com/products/openshift-local/overview) is recommended. If you're using OpenShift Local, run the following commands before starting the cluster:
```
crc config set cpus 8
crc config set memory 20000
crc config set disk-size 127
```
- The Data Grid Operator is installed
- Helm is installed and the chart repository at <https://charts.openshift.io/> has been added: `helm repo add openshift-helm-charts https://charts.openshift.io/`

### Deployment
- Connect to OpenShift:
```
oc login -u developer https://api.crc.testing:6443 
```
- Create the project:
```
oc new-project rhdg-ocp-demo
```
- As configured, both the Helm chart and the Operator use a custom JAR for loader and marshalling functionality. They also require a Secret for securing exposed endpoints. These prerequisites should be created first.
```
rm ./tmp-certs-infinispan.*
export TLS_KEYSTORE_PASSWORD=mySecret
# Create self-signed key in a PKCS12 keystore, with the password set via TLS_KEYSTORE_PASSWORD
keytool -genkeypair -storetype PKCS12 -alias infinispan -keyalg RSA -keysize 4096 -validity 365 -keystore ./tmp-certs-infinispan.p12 -dname "CN=rhdg-ocp-demo" -ext "SAN=DNS:*.rhdg-ocp-demo.apps-crc.testing,DNS:*.rhdg-ocp-demo.svc.cluster.local" -keypass $TLS_KEYSTORE_PASSWORD -storepass $TLS_KEYSTORE_PASSWORD
# Export the certificate and reimport it under a different alias, so we can use the same keystore as a truststore
keytool -exportcert -rfc -keystore ./tmp-certs-infinispan.p12 -alias infinispan -keypass $TLS_KEYSTORE_PASSWORD -storepass $TLS_KEYSTORE_PASSWORD -file ./tmp-certs-infinispan.pem
keytool -import -alias infinispan-cert -file ./tmp-certs-infinispan.pem -storetype PKCS12 -keystore ./tmp-certs-infinispan.p12 -noprompt -storepass $TLS_KEYSTORE_PASSWORD
# Apply the template, creating the keystore Secret and the server JAR provider
oc process -f ocp-yaml/cluster-prerequisites.yaml -p TLS_KEYSTORE=$(base64 -w 0 ./tmp-certs-infinispan.p12) -p TLS_KEYSTORE_PASSWORD=$TLS_KEYSTORE_PASSWORD | oc create -f -
```
- Create the Infinispan cluster, either using the Operator or Helm:
```
## Via the Data Grid Operator:

oc process -f ocp-yaml/operator-resources.yaml | oc create -f -
# To add a site for cross-site replication
oc process -f ocp-yaml/operator-resources.yaml -p SITE_NAME_LOCAL=site2 -p SITE_SUFFIX_LOCAL=-site2 -p SITE_NAME_REMOTE=site1 -p SITE_SUFFIX_REMOTE="" | oc create -f -
```
```
## Via Helm:

# Create the secret used for RHDG credentials
oc process -f ocp-yaml/helm-secret.yaml | oc create -f -
# Install the Helm chart
helm install infinispan-cluster openshift-helm-charts/redhat-data-grid --values ocp-yaml/helm-values.yaml
# Note: TLS certs are not yet implemented in the mainly RHDG Helm chart, as of this writing
# You may need to check out the latest and then run something similar to the following:
# helm install infinispan-cluster ../infinispan-helm-charts/ --values ocp-yaml/helm-values.yaml
```
- Build and deploy the client application, either within or outside 
of OCP:
```
## In OCP (uses the "openshift" Spring profile):
oc process -f ocp-yaml/client-application.yaml | oc create -f -
```
```
## Outside of OCP (uses the "local" Spring profile):
mvn spring-boot:run 
```

### Testing

The client application deployed on OpenShift will have a route exposed, or if running locally will be accessible at <https://localhost:8080>. Navigating
to the root path of the client application (the Route URL in OpenShift or <https://localhost:8080> locally) will redirect to a Swagger UI.

- Cache connection information can be viewed in the `InfinispanService.java` file in the `client` project
- Marshalling cache entries is done via Java Serialization (in `serial-cache`, with `SerialController`, 
  `SerialKey`, etc) and via Protobuf Serialization (in `proto-cache`, with `ProtoController`, `ProtoKey`, etc).
  - Java Serialization is the simplest, and uses `java.io.Serializable`.
  - Protobuf encoding requires generating Protofiles and marshallers (with `ProtoInitializer`) and registering
    the Protofiles on the RHDG cluster, and is required querying and data conversion.
  - Custom stores and remote tasks require registering the marshallers and classes on the RHDG cluster, as
    is done in this demo with Proto serialization. 
- Basic cache connectivity and functionality can be tested using the `POST`, `GET`, and `DELETE` HTTP methods on the `/serial/{key}` and `/proto/{key}` endpoints
- If a `GET /proto/{key}` is performed on a key that hasn't been stored, the custom cache loader is used to retrieve a value using the key (in this example, just by calculating the hash of the key)
- A simple remote task can be executed via the `POST /proto/removeTask/{key}` endpoint
- Querying by value can be tested via the `GET /proto/query/{queryText}` endpoint
- Cross-Site Replication can be tested with the Operator by adding data with the client, then changing `infinispan.host` property (via the `INFINISPAN_HOST` environment variable) to the other site and confirming that the data exists there.

To test with a user that fails authentication, change `INFINISPAN_USER` and `INFINISPAN_PASSWORD` in the deployment environment variables to 
use the `invalid.user` and `invalid.password` value from the secret. To test a user that authenticates but is unauthorized, use
`unauthorized.user` and `unauthorized.password`.

Cache nodes can be stopped, started, and scaled by changing the `replicas` parameter of the Data Grid operator or upgrading the Helm release 
with a new `deploy.replicas` parameter. The RHDG admin console can be accessed via an exposed Route at <https://infinispan.rhdg-ocp-demo.apps-crc.testing> 
(if using CRC), with the username `authorized` and password `Authorized-password!` (the same credentials used by the client application to 
connect to RHDG). 

### Cleanup

Resources in the project created for the demo can be deleted with these commands:

```
# Delete the cluster prerequisites
oc delete all,secret -l app=cluster-prerequisites
```
```
# Delete the Infinispan cluster installed via the Operator:
oc delete all,secret,infinispan,cache -l app=infinispan-operator
```
```
# Delete the Infinispan cluster installed via Helm:
helm uninstall infinispan-cluster
oc delete secret -l app=infinispan-helm
```
```
# Delete the client application:
oc delete all,secret -l app=client
```

The entire project can be deleted with:

```
oc delete project rhdg-ocp-demo
```

## Additional Info

### Debugging

- Infinispan CR failing to create resources, stuck in "PreliminaryChecksPassed"
  - Check the Operator pod logs for the error message "route cross-site expose type is not supported"
  - If you see that error, try deleting the Operator pod so that it is recreated
- PVC creation failing due to CRC issue preventing PVs from being recycled in OpenShift Local
  - Set the following label: `oc label  --overwrite ns openshift-infra  pod-security.kubernetes.io/enforce=privileged`
  - Manually recycle failed PVs using `oc patch pv/$PV_NAME --type json -p '[{ "op": "remove", "path": "/spec/claimRef" }]'`
- DNS lookups for routes don't work in browsers with browser-specific DNS (e.g. Brave)
  - Change browser DNS server to the system-provided DNS server (which contains entries for routes)

### Production Considerations

There are a number of design decisions that were made so that this POC would be simple and self-contained, which wouldn't necessarily be appropriate for a production application. These include:

- The application and configuration is all added to openshift via "oc apply", rather than a CI/CD pipeline 
- The server JAR artifact should be stored in an artifact repository (e.g. JFrog), rather than an HTTPD container
- The Cache configuration would likely be part of the client application source code, and updated in the RHDG cluster as part of the client CI/CD deployment
- Cache authentication is configured via Secrets, but Production environments might use a centralized permission repository (e.g. LDAP)

### Accessing RHDG outside of OpenShift

This demo includes instructions on how to connect to RHDG from outside of OCP. This does introduce a few design considerations:

- There are a number ingress methods for connecting to the RHDG cluster, based on design requirements:
  - [NodePorts](https://docs.openshift.com/container-platform/4.12/networking/configuring_ingress_cluster_traffic/configuring-ingress-cluster-traffic-nodeport.html)
  - [LoadBalancers](https://docs.openshift.com/container-platform/4.12/networking/configuring_ingress_cluster_traffic/configuring-ingress-cluster-traffic-load-balancer.html)
  - [Routes](https://docs.openshift.com/container-platform/4.12/networking/routes/route-configuration.html) (used for this demo)
    - Note that Hot Rod connections over routes MUST use passthrough encryption, otherwise the connection will be broken with "invalid 
      magic byte" errors. This is because Hot Rod is not an HTTP protocol, and Routes expect unencrypted connections to be HTTP. See 
      [this solution article](https://access.redhat.com/solutions/6134351) for details.
- Connections to RHDG from outside of OCP must be made with BASIC client intelligence, meaning requests will simply be load balanced 
rather than sent to the entry's owner node. This can have a few performance and functional impacts:
  - Cache loaders may be called multiple times for each cache entry
  - There will be an additional network hop when a request is forwarded from a non-owner node to the entry owner
  - Bulk operations (like keySet and size) may return incorrect results when using a cache loader that doesn't implement the BULK_READ 
    methods (such as the CustomStore loader in this demo)

### Links

Application client code derived from <https://github.com/ngecom/openshiftSpringBoot>

[OpenShift Local](https://developers.redhat.com/products/openshift-local/overview)

[RHDG Operator Guide](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/html/data_grid_operator_guide/index)

[RHDG Operator custom code deployment](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/guide/1cfa1bfa-697d-4fda-9e0a-8c3e2b99f815)

[Building and deploying Data Grid clusters with Helm](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/html-single/building_and_deploying_data_grid_clusters_with_helm/index)

[Latest Infinispan Helm Chart](https://github.com/infinispan/infinispan-helm-charts)

