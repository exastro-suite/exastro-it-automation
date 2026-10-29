UPDATE T_COMN_VERSION 
SET ADDITIONAL_DRIVER = JSON_ARRAY_APPEND(
    ADDITIONAL_DRIVER, 
    '$', 
    JSON_OBJECT(
        'id', 'ai_assistant',
        'name', 'Exastro AI Assistant',
        'description_ja', '',
        'description_en', ''
    )
),
INSTALLED_DRIVER_JA = JSON_SET(
    INSTALLED_DRIVER_JA,
    '$.ai_assistant','Exastro AI Assistant'
),
INSTALLED_DRIVER_EN = JSON_SET(
    INSTALLED_DRIVER_EN,
    '$.ai_assistant','Exastro AI Assistant'
),
LAST_UPDATE_TIMESTAMP = CURRENT_TIMESTAMP
WHERE NOT JSON_CONTAINS(ADDITIONAL_DRIVER, '{"id": "ai_assistant"}');

-- 既存のオーガナイゼーションは、生成AIサービス無効で初期設定
UPDATE T_COMN_ORGANIZATION_DB_INFO
SET NO_INSTALL_DRIVER = 
  CASE 
    WHEN NO_INSTALL_DRIVER IS NULL THEN 
      '["ai_assistant"]'
    WHEN JSON_CONTAINS(NO_INSTALL_DRIVER, '"ai_assistant"') = 0 THEN 
      JSON_ARRAY_APPEND(NO_INSTALL_DRIVER, '$', 'ai_assistant')
    ELSE 
      NO_INSTALL_DRIVER
  END;