ARG ANSIBLE_AGENT_IMAGE
ARG ANSIBLE_AGENT_IMAGE_TAG

FROM ${ANSIBLE_AGENT_IMAGE}:${ANSIBLE_AGENT_IMAGE_TAG}


## Add module command bellow, if you need to use extend ansible module.

# Example:
# RUN ansible-galaxy collection install amazon.aws \
#  &&  pip3.12 install --upgrade boto3 botocore
