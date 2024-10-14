# JBoss EAP 8 on OCP Demo

This application is a simple demonstration of some features of JBoss EAP 8 on OpenShift Container Platform.

## Overview

### Demonstrated Features

- S2I deployment via Helm Chart
- Deployment of existing, third-party binaries
- Custom EAP server configuration

### Project Layout

The directory structure is mostly laid out like any standard Maven project, with the `src` directory,
`pom.xml`, etc. 

In addition to the standard directories, there's an `.s2i` directory which contains S2I-specific 
files, an `extensions` directory (pointed to by the `.s2i/environment` configuration file) 
which contains additional configuration scripts that run on the JBoss EAP container during build
and startup, and the `templates` directory containing YAML files. These are described in detail
later in this README.

### Prerequisites

- Access to an OpenShift cluster. For local testing, [OpenShift Local](https://developers.redhat.com/products/openshift-local/overview) is recommended. 
- Helm is installed and the chart repository at <https://jbossas.github.io/eap-charts/> has been added: `helm repo add jboss-eap https://jbossas.github.io/eap-charts/`

Run the following commands to connect to your cluster and create a namespace:
```
oc login -u developer https://api.crc.testing:6443 
oc new-project jboss-eap-ocp-demo
```

## S2I 

This section describes how to perform S2I builds and deployments of an EAP container image, using this repository's
application source. The application listens on port 8080 which is exposed with a Route, with port 8888 used for 
JGroups cluster via KUBE_PING and the `*-ping` Service.

### S2I via Helm

S2I builds and deployments are performed using the EAP Helm Chart. This is done via the following command, and installs using the Helm parameters file located in `templates/helm-s2i.yaml`:

```
helm install helm-s2i -f ocp-yaml/helm-s2i.yaml jboss-eap/eap8
```

This will create a BuildConfig that builds the application WAR, including the Maven build and running `extensions/install.sh`. This will involve fetching the JBoss EAP 8 binaries, as configured using the [EAP Maven plugin](https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#assembly_provisioning-a-jboss-eap-server-using-the-maven-plugin_default
). The completed binaries, both the WAR and the EAP libraries, are then sent as input to another Build, which creates the application image.

The Helm chart also configures a Deployment, Services, and a Route. Ultimately, the application should be accessible at the Route URL, e.g. <https://helm-s2i-jboss-eap-ocp-demo.apps-crc.testing/>

Further documentation is available [here](https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#proc_building-applications-images-using-source-to-image-s2i-on-openshift_assembly_building-and-running-jboss-eap-applicationson-openshift-container-platform).

### S2I via Template

Builds and deployments can also be explicitly created via a Template. This can be useful for greater control over build
and deployment details, such as using a single build rather than chained builds.

To create a template using chained S2I builds, run:

```
oc process -f ocp-yaml/template-s2i-chained.yaml | oc create -f -
```

For a single, non-chained build, run:

```
oc process -f ocp-yaml/template-s2i-single.yaml | oc create -f -
```

As with the Helm installation, these will create BuildConfig(s), a Deployment, Services, and a Route. The application will
be accessible at <> and <>.

## Third-party Provided Artifact

Some uses cases involve a compiled artifact (EAR, WAR, etc) provided by a third party vendor. In this case, the compiled artifact is provided to a builder image that fetches the EAP runtime libraries and then copies the artifact into the `standalone/deployments` directory.

First, run a Maven build locally, so we have a WAR to serve as a provided artifact:

```
mvn clean install
```

This results in the WAR being created in `target/demo-webapp.war`. Then, create the "third-party" template in OpenShift, and start a build using the compiled WAR as input:

```
oc process -f ocp-yaml/template-third-party.yaml | oc create -f -
oc start-build third-party --from-file=target/demo-webapp.war
```

This builds a container using the Dockerfile defined in `templates/third-party.yaml`, and uses the provided WAR. The template also contains the Deployment, Service, and Route, so it should eventually be accessible, e.g. <https://third-party-rhdg-ocp-demo.apps-crc.testing/>

## Cleanup

```
# Delete the application built via Helm S2I
helm uninstall helm-s2i
# Delete the application built via chained S2I template
oc delete all -l app=s2i-chained
# Delete the application built via unchained S2I template
oc delete all -l app=s2i-single
# Delete the application built via third-party provided WAR
oc delete all -l app=third-party
```

## Links

- [JBoss EAP 8 on OpenShift](https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html/using_jboss_eap_on_openshift_container_platform/index)
- <https://github.com/Azure-Samples/tomcat10-jakartaee9> (original application source code)
