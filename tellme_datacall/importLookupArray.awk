# ------- INSTRUCTIONS:
#
# use within the folder containing city folders, decodificheConcetti.tsv, decodificheCities.tsv.
# The script is designed to be called this way:
#
# tree -if --noreport | grep shp | awk -f importLookupArray.awk
#
# the script outputs the command lines to invoke geonode importlayers script 
# 
# the output can be piped to bash in order for the sentences to be executed (each line starts with
# "docker-compose exec django" in order to be executed in the get-it django container from the host)
#
# Side effect: the file "importOutputLog.txt" is written in the execution folder with some details.
# --------
#
# TODO: integrate layer styling through geoserver rest api. The following should set the default style for a layer. (note: it could be one of different strategies).
#       Investigate which layer name should we use (is it the "name" set in the following importlayers command option or other? something like "geonode:<name>"?
#
# curl -v -u username:password -X PUT -H "Content-type: text/xml" -d "<layer><defaultStyle><name>islandarea</name> </defaultStyle><enabled>true</enabled></layer>" http://localhost:8080/geoserver/rest/layers/geonode:islandarea
#
#
BEGIN{
  while(getline < "decodificheConcetti.tsv"){
    split($0,ft,"\t")
    conceptname=ft[1];
    conceptslug=sprintf("concept_%d",ft[2]);
    currentname=ft[3];#bisogna aggiungere colonna con valori attuali della HK corrispondente a concept_X;
    label2conceptslug[conceptname]=conceptslug;
    conceptslug2currentname[conceptslug]=currentname;
    conceptslug2conceptid[conceptslug]=ft[2];
  }
  close("decodificheConcetti.tsv");
  while(getline < "decodificheCities.tsv"){
    split($0,ft,"\t");
    cityname=ft[1];
    cityabbrev=ft[2];
    city2cityabbrev[cityname]=cityabbrev;    
    city2region[cityname]=ft[3];
  }
  close("decodificheCities.tsv");
  FS="/";
}
{
  city=$2;
  user=city; # NOTE: currently each city team has a user whose id is the city name capitalized (written exactly as the first column of "decodificheCities.tsv" file)
  protocol=$3;
  keyword=$4;
  relatedConcept=$5;
  
  protocolid=1; #TODO: change this for upcoming protocols in the future. Use a lookup table like the ones for cities and concepts
  
  l=split(protocol,protocolsplit,"_");
  scale=protocolsplit[l];

  conceptslug=label2conceptslug[relatedConcept];
  currentconceptname=conceptslug2currentname[conceptslug]; 
  cityabbrev=city2cityabbrev[city];
  cityprefix=sprintf("%s_", cityabbrev);
  region=city2region[city];
  conceptid=conceptslug2conceptid[conceptslug];
  

  row=sprintf("city: %s\tprotocol: %s\tconcept: %s\tslug: %s", city, protocol, relatedConcept, conceptslug);
  print row > "importOutputLog.txt";
  split($6,filename,".");
  layertitle=filename[1];
  sub(/\\ /,"_",layertitle);
  if(index(layertitle,cityprefix)==0){
    layertitle=sprintf("%s%s", cityprefix, layertitle)
  }

  output=sprintf("docker-compose exec django python manage.py importlayers --keywords=%s --user=%s --title=%s --regions=%s --charset=UTF-8 %s", currentconceptname, user, layertitle, region, $0);
  print output;

  postproduction=sprintf("add here commands to associate styles to the layer. Layer: %s\tConcept_id:%s\tProtocol (i.e. protocol and scale, to be looked up): %s", layertitle, conceptslug, protocol);
  print postproduction > "importOutputLog.txt";

  geoserver_username="admin";
  geoserver_password="geoserver";
  stylename=sprintf("p_%s-c_%s-s_%s",protocolid,conceptid,scale);
  geoserver_layername=sprintf("geonode:%s",layertitle);
  getit_FQDN="tellmehub.get-it.it";
  geoserverAPI_CURL_command=sprintf("curl -v -u %s:%s -X PUT -H \"Content-type: text/xml\" -d \"<layer><defaultStyle><name>%s</name> </defaultStyle><enabled>true</enabled></layer>\" http://%s/geoserver/rest/layers/%s", geoserver_username, geoserver_password, stylename, getit_FQDN, geoserver_layername);

  print geoserverAPI_CURL_command > "postproduction_curl_statement.txt";

}

END{
  
  close("postproduction_curl_statement.txt")
  close("importOutputLog.txt")
}
