import yaml
yamlfile = 'a.yml'
retParse = yaml.load(open(yamlfile).read(), Loader=yaml.FullLoader)
print(retParse)
#for key in retParse:
#    print(key)
#    if type(key) in (dict, list):
#        print('error')
