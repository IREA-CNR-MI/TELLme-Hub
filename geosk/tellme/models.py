from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer

def get_associated_tellme_relatedConcepts(self):
    maplayers=self.layers
    m=self

    l_set = set(Layer.objects.filter(alternate__in={l.layer_title for l in m.layers if l.group != 'background'}))
    lista = []

    for l in l_set:
        lista.extend(l.keywords.all())


    k_set = set(lista)

    #[(k.slug, k.name) for k in k_set if (k.get_root()).name == 'TELLme']

    #[(k.get_parent().name, k.name) for k in k_set if (k.get_root()).name == 'TELLme']
    tellme_keywords={}
    for kc in [(k.get_parent().name, k.name) for k in k_set if (k.get_root()).name == 'TELLme']:
        if kc[0] not in tellme_keywords.keys():
            tellme_keywords[kc[0]] = []
        tellme_keywords[kc[0]].append(kc[1])

    ''' example usage 
    
    for k in tellme_keywords:
        print(k)
        for c in tellme_keywords[k]:
            print("  " + c)
            
    '''
    return tellme_keywords

#    return 'tellmeProject'


Map.get_associated_tellme_relatedConcepts = get_associated_tellme_relatedConcepts
