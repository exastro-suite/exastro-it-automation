-- ALTER: -2.1.1
    -- T_COMN_OPERATION

-- オペレーション一覧
ALTER TABLE T_COMN_OPERATION ADD LANGUAGE VARCHAR(40) NULL AFTER ENVIRONMENT;
ALTER TABLE T_COMN_OPERATION_JNL ADD LANGUAGE VARCHAR(40) NULL AFTER ENVIRONMENT;
