#!/usr/bin/env bash

# Runs during image build, used to e.g. copy custom module libraries
# See https://docs.redhat.com/en/documentation/red_hat_jboss_enterprise_application_platform/8.0/html-single/using_jboss_eap_on_openshift_container_platform/index#using_install_sh_to_execute_custom_scripts
echo "Running $PWD/install.sh"
