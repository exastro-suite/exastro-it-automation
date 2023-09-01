class T_EVRL_EVENT_COLLECTION_PROGRESS:
    def __init__(self, DBObj):
        self.DBObj = DBObj
        self.List  = []
        # select * from T_EVRE_EVENT_COLLECTION_PROGRESS where evaluated_flag = '0' AND DISUSE_FLAG = '0' order by fetched_time DESC
        array = {"EVENT_COLLECTION_ID": "1","FETCHED_TIME": "200001010000", "EVALUATED_FLAG":"0"}
        self.List.append(array)

    def getT_EVRL_EVENT_COLLECTION_PROGRESS(self):
        return self.List

    # evaluated_flagをONに設定
    def setUsedT_EVRL_EVENT_COLLECTION_PROGRESS(self, Rows):
        event_collection_ids = ''
        for Row in Rows:
            if len(event_collection_ids) != 0:
                event_collection_ids += ","
            event_collection_ids += '"%s"' % format(Row['EVENT_COLLECTION_ID'])
        # update T_EVRE_EVENT_COLLECTION_PROGRESS set evaluated_flag = '1' where event_collection_id in (%s)
        return True

        

#DBObj = ''
#obj = T_EVRL_EVENT_COLLECTION_PROGRESS(DBObj)
#print(obj.getEventCollectionProgress())
