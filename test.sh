#! /bin/bash


ALL_PARAMS=$@
VENV_ACTIVATION_SCRIPT=$1
UNITTEST_PARAMS=${ALL_PARAMS#* }

set_config_variables() {
# Set example environment variables as default settings for testing
pattern="^[A-Za-z].*=.*$"

while read ; do
  if [[ ${REPLY} =~ ${pattern} ]]; then
    export ${REPLY}
  fi
done < ./.example.env

}

source ${VENV_ACTIVATION_SCRIPT} && set_config_variables  && python -m unittest ${UNITTEST_PARAMS}  && deactivate
