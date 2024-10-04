# JBoss EAP 8 Sample

TODO complete all of this

https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#assembly_deploying-a-third-party-application-on-openshift_assembly_building-and-running-jboss-eap-applicationson-openshift-container-platform

https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#assembly_provisioning-a-jboss-eap-server-using-the-maven-plugin_default

https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#proc_building-applications-images-using-source-to-image-s2i-on-openshift_assembly_building-and-running-jboss-eap-applicationson-openshift-container-platform

oc process -f templates/third-party.yaml | oc create -f -

oc start-build third-party --from-file=target/helloworld.war

helm install helm-s2i -f ./templates/helm-s2i.yaml jboss-eap/eap8


oc delete all -l app=third-party
oc delete all -l app=helm-s2i
