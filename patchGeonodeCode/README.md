# Patch bug causing issue when adding remote layer to map
### copy the following file out of the docker container
docker cp django4starterkit:/usr/local/lib/python2.7/site-packages/geonode/maps/views.py ./
cp views.py maps.views.patched.py
### edit the file at line 864.
Substitute

                                 layer_params=json.dumps(config),
with 
                                 layer_params=json.dumps(config, cls=DjangoJSONEncoder)
### copy the patched file back in the container
docker cp maps.views.patched.py django4starterkit:/usr/local/lib/python2.7/site-packages/geonode/maps/views.py

### restart the container
cd ..
docker-compose restart django

