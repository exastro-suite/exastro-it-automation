UPDATE T_TERC_IF_INFO     SET TERRAFORM_REFRESH_INTERVAL=1000 WHERE TERRAFORM_IF_INFO_ID='1' AND TERRAFORM_REFRESH_INTERVAL=3000;
UPDATE T_TERC_IF_INFO_JNL SET TERRAFORM_REFRESH_INTERVAL=1000 WHERE TERRAFORM_IF_INFO_ID='1' AND TERRAFORM_REFRESH_INTERVAL=3000;
