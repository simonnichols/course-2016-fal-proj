import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from bson.code import Code
from bson.json_util import dumps
from helpers import *


class merge(dml.Algorithm):
    contributor = 'aydenbu_huangyh'
    reads = ['aydenbu_huangyh.zip_communityGardens_count',
             'aydenbu_huangyh.zip_hospitals_count',
             'aydenbu_huangyh.zip_Healthycornerstores_count']
    writes = ['aydenbu_huangyh']

    @staticmethod
    def execute(trial = False):

        startTime = datetime.datetime.now()

        # Set up the database connection
        repo = openDb(getAuth("db_username"), getAuth("db_password"))

        # Get the collections
        hospitals = repo['aydenbu_huangyh.zip_hospitals_count']
        stores = repo['aydenbu_huangyh.zip_Healthycornerstores_count']


        # For every document in hospitals zip find the number of store that associate with that zip
        zip_health = []
        for document in hospitals.find():
            stores_count = stores.find_one({'_id': document['_id']}, {'_id': False, 'value.numofStore': True})
            if stores_count is None:
                zip = {'_id': document['_id'],
                        'value': {
                            'numofHospital': document['value']['numofHospital'],
                            'numofStore': 0.0}
                       }
                zip_health.append(zip)
                continue
            else:
                zip = {'_id': document['_id'],
                        'value': {
                            'numofHospital': document['value']['numofHospital'],
                            'numofStore': stores_count['value']['numofStore']}
                       }
                zip_health.append(zip)
        ''''''''''''''''''''''''''''''''''''''''''''''''


        # Create a new collection and insert the result data set
        repo.dropPermanent("zip_health")
        repo.createPermanent("zip_health")
        repo['aydenbu_huangyh.zip_health'].insert_many(zip_health)

        repo.logout()
        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}





    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):

        # Set up the database connection
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('aydenbu_huangyh', 'aydenbu_huangyh')

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        '''
        '''
        # The agent
        this_script = doc.agent('alg:aydenbu_huangyh#merge_store_hospital',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})

        # The source entity
        store_source = doc.entity('dat:healthy_corner_store_count',
                              {'prov:label': 'HealthyCorner Store Count', prov.model.PROV_TYPE: 'ont:DataResource',
                               'ont:Extension': 'json'})
        hospital_source = doc.entity('dat:hospital_count',
                                  {'prov:label': 'Hospital Count', prov.model.PROV_TYPE: 'ont:DataResource',
                                   'ont:Extension': 'json'})

        # The activity
        get_zip_health = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime,
                                               {prov.model.PROV_LABEL: "Merge the numbers of hospital and HealthyStore in each zip"})

        # The activity is associated with the agent
        doc.wasAssociatedWith(get_zip_health, this_script)

        # Usage of the activity: Source Entity
        doc.usage(get_zip_health, store_source, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Computation'})
        doc.usage(get_zip_health, hospital_source, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Computation'})

        # The Result Entity
        zip_health = doc.entity('dat:aydenbu_huangyh#zip_health',
                                            {prov.model.PROV_LABEL: 'Zip Health',
                                             prov.model.PROV_TYPE: 'ont:DataSet'})

        # Result Entity was attributed to the agent
        doc.wasAttributedTo(zip_health, this_script)

        # Result Entity was generated by the activity
        doc.wasGeneratedBy(zip_health, get_zip_health, endTime)

        # Result Entity was Derived From Source Entity
        doc.wasDerivedFrom(zip_health, store_source, get_zip_health, get_zip_health,
                           get_zip_health)
        doc.wasDerivedFrom(zip_health, hospital_source, get_zip_health, get_zip_health,
                           get_zip_health)

        repo.record(doc.serialize())
        repo.logout()

        return doc

merge.execute()
doc = merge.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))