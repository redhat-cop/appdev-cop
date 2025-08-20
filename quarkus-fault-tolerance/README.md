
# Fault Tolerance Demo

This project demonstrates some features that can be used to ensure fault tolerance in containerized, cloud-native applications.

This repository was cloned from [quarkusio/quarkus-quickstarts](https://github.com/quarkusio/quarkus-quickstarts).

## Overview

### Scope

The following features are explored in this application:

- Kubernetes Probes
- MicroProfile Health Checks
- MicroProfile Fault Tolerance

### Design

This demo consists of three parts: a Redis backend acting as a datastore, a "backend" Quarkus application that connects to Redis,
and a "frontend" Quarkus application that connects to the backend. The frontend could be implemented as a UI, but we'll just be
using Swagger here.

## Running the demo

### Prerequisites

- Access to an OpenShift cluster. For local testing, [OpenShift Local](https://developers.redhat.com/products/openshift-local/overview) is recommended
- The OpenShift cluster must have the `redis:latest` image in the `openshift` namespace (which it should be default)

### Deployment

- Update the git URLs in `templates/setup.yaml` if you want to use a different git repository. 
- Connect to OpenShift:
```
oc login -u developer https://api.crc.testing:6443 
```
- Create the project and project resources:
```
oc new-project fault-tolerance-demo
oc process -f templates/setup.yaml | oc apply -f -
```

This will perform a Quarkus native build, and deploy the three components to your OpenShift cluster. `frontend` and `backend` will be exposed
via Routes, e.g.:
- <https://frontend-fault-tolerance-demo.apps-crc.testing>
- <https://backend-fault-tolerance-demo.apps-crc.testing>

### Testing

#### Basic Functionality

When the applications are running, you can navigate to the Swagger UIs in order to check their REST API:

- <https://frontend-fault-tolerance-demo.apps-crc.testing/q/swagger-ui/>
- <https://backend-fault-tolerance-demo.apps-crc.testing/q/swagger-ui/>

You can also observe their health check endpoints, implemented via SmallRye Health (an implementation of MicroProfile Health):

- <https://frontend-fault-tolerance-demo.apps-crc.testing/q/health/>
- <https://backend-fault-tolerance-demo.apps-crc.testing/q/health/>

#### Simulating Failures

Run the following command to bring down the Redis instance, simulating a DB crash:

```
oc patch deployment db -p '{"spec": {"replicas": 0}}'
```

On the backend server, `RedisConnectionHealthCheck` (which calls the Redis datasource) will start returning failures. This
class, annotated with `@Readiness` and implementing `HealthCheck`, is used by SmallRye Health to construct the page located
at `/q/health/ready`. With Redis down, loading this page will start returning error HTTP status codes.

The `backend` deployment is configured to use this health check page in its readiness probe, so once the page starts returning
errors, the pods in that deployment will be marked as unready, and will not be accessible via the Service or Route. Fortunately,
`frontend` is configured to be resilient to an outage in `backend`, using SmallRye Fault Tolerance. 

The `IncrementResource` class in `frontend` is configured with a fallback for the `keys` method. So, the `frontend` application
is still accessible, and the GET `/increments` call will still succeed, though it will return dummy, fallback data:

```
[
  "dummy response"
]
```

To reenable the Redis datasource, run the following command:

```
oc patch deployment db -p '{"spec": {"replicas": 1}}'
```

### Cleanup

The project can be deleted with:

```
oc delete project fault-tolerance-demo
```

### Links

Application client code derived from <https://github.com/quarkusio/quarkus-quickstarts>

[Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

[SmallRye Health](https://quarkus.io/guides/smallrye-health)

[SmallRye Fault Tolerance](https://quarkus.io/guides/smallrye-fault-tolerance)
