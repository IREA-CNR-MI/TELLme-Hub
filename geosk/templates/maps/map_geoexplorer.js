{% include 'geonode/ext_header.html' %}
{% include 'geonode/geo_header.html' %}
<style type="text/css">
#aboutbutton {
    display: none;
}
#paneltbar {
    margin-top: 81px;
}
button.logout {
    display: none;
}
button.login {
    display:none;
}
.map-title-header {
    margin-right: 10px;
}
</style>

<style type="text/css">

#externalContainerSemantics{
    display: block;
    height: 99%;
    padding:2px;
}
#tellme_panelContainer{
    overflow: auto;
    display: block;
    /*padding: 15px;*/
    border: 1px solid #8B008B;
    border-radius: .9rem;
    height: inherit;
}

#tellme_panelContainer .titolo{
    padding:10px;
}

#ul_tellme_semantics{
    font-size: 10px!important;
    padding:10px;
}

/* tellme keywords (title of each sublist of concepts) */
.li_tellme_keyword{
    cursor:pointer;
    font-weight:bold;
    text-transform:uppercase;
    margin-bottom:.1rem;
}

.li_tellme_keyword.on::after{
    content: " <<"
}

.li_tellme_keyword:hover{
    color:#2e89a6;
}

.conceptToggle {
    padding: 4px 0 4px 8px;
    background-color:#fff;
    color:#212529;
    display:block;
    cursor:pointer;
}

.conceptToggle.active {
    background-color: #8B008B;
    color: #fff;
}

.ul_tellme_concepts{
    display:block;
    /*width:200px;
    float:left;*/
}

.ul_tellme_concepts > .active:first-of-type{
border-top-left-radius:.25rem;
border-top-right-radius:.25rem;
}

.ul_tellme_concepts > .active:last-of-type{
border-bottom-left-radius:.25rem;
border-bottom-right-radius:.25rem;
}





</style>

<link href="{{ STATIC_URL}}geonode/css/geoexplorer/map_geoexplorer.css" rel="stylesheet"/>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-mixin.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/Geonode-CatalogueApiSearch.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/extjs/GeoNode-GeoExplorer.js"></script>
<script type="text/javascript" src="{{ STATIC_URL}}geonode/js/utils/thumbnail.js"></script>
<script src="{{ STATIC_URL}}tellme/jquery.min.js"></script>
<script type="text/javascript">
var app;


/*
var pannello='<li class="list-group-item">'+
'          <h4 class="list-group-item-heading">TELLme semantics"</h4>'+
'          <p>This map relates to the following concepts:</p>'+
'          <ul class="list-unstyled">'+
{% for keyword, concepts in map.get_associated_tellme_relatedConcepts.items %}
'              <li>{{ keyword }}</li>'+
{% for concept in concepts %}
'              <li>- {{ concept }}</li>'+
{% endfor %}
{% endfor %}
'          </ul>'+
'       </li>';
*/
{% autoescape off %}
var pannello="<div id='externalContainerSemantics'><div id='tellme_panelContainer'><div class='titolo'>TELLme semantics</div>{{map.panel_concept_selection_html}}</div></div>"
{% endautoescape %}


//tweak Geoext.tree.LayerNodeUI in order to set some class for checkboxes

GeoExt.tree.LayerNodeUI.prototype.render=function(bulkRender){
    //Ext.override('GeoExt.tree.LayerNodeUI',{
      //  render: function(bulkRender){
            //this.callOverridden();
            //a=this.node.attributes;
            //alert("qui");
            //console.log(a);
            //*
            //var l2c={{map.get_associated_tellme_relatedConcepts.items}}

            var l2c=function (layername){
                var concepts=[];
                {% for l_title, concepts in map.dict_layer_title_2_tellme_concepts.items %}
                if (layername==="{{l_title}}"){{% for concept in concepts %}
                    concepts.push("{{concept}}");{% endfor %}
                }
                {% endfor %}
                return(concepts.join(" "));
            }

            var a = this.node.attributes;
            console.log(a);
            if (a.checked === undefined) {
                a.checked = this.node.layer.getVisibility();
            }
            if (a.disabled === undefined && this.node.autoDisable) {
                this.node.disabled = this.node.layer.inRange === false || !this.node.layer.calculateInRange();
            }
            GeoExt.tree.LayerNodeUI.superclass.render.apply(this, arguments);
            var cb = this.checkbox;
            if(a.checkedGroup) {
                // replace the checkbox with a radio button
                var radio = Ext.DomHelper.insertAfter(cb,
                    ['<input type="radio" name="', a.checkedGroup,
                    '_checkbox" class="', cb.className,
                    cb.checked ? '" checked="checked"' : '',
                    '"></input>'].join(""));
                radio.defaultChecked = cb.defaultChecked;
                Ext.get(cb).remove();
                this.checkbox = radio;
            }
            else{
                cb.className=l2c(a.layer.name);
                cb.id=["cb_layername_",a.layer.name].join("_");
            }
            this.enforceOneVisible();
            //*/
        }
    //});


GeoExplorer.Composer.prototype.initPortal= function() {


        var westPanel = new gxp.CrumbPanel({
            id: "tree",
            region: "center",//"west",
            width: 320,
            split: true,
            collapsible: true,
            collapseMode: "mini",
            hideCollapseTool: true,
            header: false
        });

        var westPanelExternal = new Ext.Panel({
            id:"westContainer",
            region:"west",
            width:320,
            split:true,
            collapsible: true,
            collapseMode: "mini",
            hideCollapseTool: true,
            header: false,
            layout:"border",
            items: [
                westPanel,
                {
                    region: "south",
                    id:"tellme-panel-container",
                    html:pannello,
                    paddings: '0 5 15 15',
                    title: "TELLme",
                    header:false,
                    //layout:"fit",
                    minHeight: 150,
                    maxHeight: 5000,
                    height: 190,
                    split: true,
                    collapsible: true,
                    collapseMode: "mini",
                    hideCollapseTool: true
                }
            ]
        });
        /*//
        var eastPanel = new Ext.Panel({
            region: "east",
            id: "east",
            height: 220,
            width:320,
            //border: false,
            split: true,
            collapsible: true,
            collapseMode: "mini",
            collapsed: false,
            hideCollapseTool: true,
            header: false,
            layout: "border",
            items: [
                {
                    region: "center",
                    id:"tellme-panel-container",
                    title: "TELLme",
                    header:false,
                    layout:"fit"
                }
            ]
        });
        //*/
        var southPanel = new Ext.Panel({
            region: "south",
            id: "south",
            height: 220,
            border: false,
            split: true,
            collapsible: true,
            collapseMode: "mini",
            collapsed: true,
            hideCollapseTool: true,
            header: false,
            layout: "border",
            items: [
            {
                region: "center",
                id: "table",
                title: this.tableText,
                layout: "fit"
            }, {
                region: "west",
                width: 320,
                id: "query",
                title: this.queryText,
                split: true,
                collapsible: true,
                collapseMode: "mini",
                collapsed: true,
                hideCollapseTool: true,
                layout: "fit"
            }]
        });
        var toolbar = new Ext.Toolbar({
            disabled: true,
            id: 'paneltbar',
            items: []
        });
        this.on("ready", function() {
            // enable only those items that were not specifically disabled
            var disabled = toolbar.items.filterBy(function(item) {
                return item.initialConfig && item.initialConfig.disabled;
            });
            toolbar.enable();
            disabled.each(function(item) {
                item.disable();
            });
        });

        var googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: this.mapPanel,
            id: "globe",
            tbar: [],
            listeners: {
                beforeadd: function(record) {
                    return record.get("group") !== "background";
                }
            }
        });

        // TODO: continue making this Google Earth Panel more independent
        // Currently, it's too tightly tied into the viewer.
        // In the meantime, we keep track of all items that the were already
        // disabled when the panel is shown.
        var preGoogleDisabled = [];

        googleEarthPanel.on("show", function() {
            preGoogleDisabled.length = 0;
            toolbar.items.each(function(item) {
                if (item.disabled) {
                    preGoogleDisabled.push(item);
                }
            });
            toolbar.disable();
            // loop over all the tools and remove their output
            for (var key in this.tools) {
                var tool = this.tools[key];
                if (tool.outputTarget === "map") {
                    tool.removeOutput();
                }
            }
            var layersContainer = Ext.getCmp("tree");
            var layersToolbar = layersContainer && layersContainer.getTopToolbar();
            if (layersToolbar) {
                layersToolbar.items.each(function(item) {
                    if (item.disabled) {
                        preGoogleDisabled.push(item);
                    }
                });
                layersToolbar.disable();
            }
        }, this);

        googleEarthPanel.on("hide", function() {
            // re-enable all tools
            toolbar.enable();

            var layersContainer = Ext.getCmp("tree");
            var layersToolbar = layersContainer && layersContainer.getTopToolbar();
            if (layersToolbar) {
                layersToolbar.enable();
            }
            // now go back and disable all things that were disabled previously
            for (var i=0, ii=preGoogleDisabled.length; i<ii; ++i) {
                preGoogleDisabled[i].disable();
            }

        }, this);

        this.mapPanelContainer = new Ext.Panel({
            layout: "card",
            region: "center",
            defaults: {
                border: false
            },
            items: [
                this.mapPanel,
                googleEarthPanel
            ],
            activeItem: 0
        });

        this.portalItems = [{
            region: "center",
            layout: "border",
            tbar: toolbar,
            items: [
                this.mapPanelContainer,
                westPanelExternal, //westPanel,
                southPanel
                //,eastPanel
            ]
        }];

        GeoExplorer.Composer.superclass.initPortal.apply(this, arguments);
    }


Ext.onReady(function() {
{% autoescape off %}
    GeoExt.Lang.set("{{ LANGUAGE_CODE }}");
    var config = Ext.apply({
        authStatus: {% if user.is_authenticated %} 200{% else %} 401{% endif %},
        {% if PROXY_URL %}
        proxy: '{{ PROXY_URL }}',
        {% endif %}

        {% if 'access_token' in request.session %}
        access_token: "{{request.session.access_token}}",
        {% else %}
        access_token: null,
        {% endif %}

        {% if MAPFISH_PRINT_ENABLED %}
        printService: "{{GEOSERVER_BASE_URL}}pdf/",
        {% else %}
        printService: null,
        printCapabilities: null,
        {% endif %}

        /* The URL to a REST map configuration service.  This service
         * provides listing and, with an authenticated user, saving of
         * maps on the server for sharing and editing.
         */
        rest: "{% url "maps_browse" %}",
        ajaxLoginUrl: "{% url "account_ajax_login" %}",
        homeUrl: "{% url "home" %}",
        localGeoServerBaseUrl: "{{ GEOSERVER_BASE_URL }}",
        localCSWBaseUrl: "{{ CATALOGUE_BASE_URL }}",
        csrfToken: "{{ csrf_token }}",
        tools: [{ptype: "gxp_getfeedfeatureinfo"}],
        listeners: {
            "ready": function() {
                app.mapPanel.map.getMaxExtent = function() {
                    return new OpenLayers.Bounds(-80150033.36/2,-80150033.36/2,80150033.36/2,80150033.36/2);
                }
                app.mapPanel.map.getMaxResolution = function() {
                    return 626172.135625/2;
                }
                l = app.selectedLayer.getLayer();
                l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent(), restrictedExtent:app.mapPanel.map.getMaxExtent()});

                {% if 'access_token' in request.session %}
                    try {
                        l.url += ( !l.url.match(/\b\?/gi) || l.url.match(/\b\?/gi).length == 0 ? '?' : '&');

                        if((!l.url.match(/\baccess_token/gi))) {
                            l.url += "access_token={{request.session.access_token}}";
                        } else {
                            l.url =
                                l.url.replace(/(access_token)(.+?)(?=\&)/, "$1={{request.session.access_token}}");
                        }
                    } catch(err) {
                        console.log(err);
                    }
                {% endif %}

                for (var ll in app.mapPanel.map.layers) {
                    l = app.mapPanel.map.layers[ll];
                    if (l.url && l.url.indexOf('{{GEOSERVER_BASE_URL}}') !== -1) {
                        l.addOptions({wrapDateLine:true, displayOutsideMaxExtent: true});
                        l.addOptions({maxExtent:app.mapPanel.map.getMaxExtent(), restrictedExtent:app.mapPanel.map.getMaxExtent()});
                        {% if 'access_token' in request.session %}
                            try {
                                    l.url += ( !l.url.match(/\b\?/gi) || l.url.match(/\b\?/gi).length == 0 ? '?' : '&');

                                    if((!l.url.match(/\baccess_token/gi))) {
                                        l.url += "access_token={{request.session.access_token}}";
                                    } else {
                                        l.url =
                                            l.url.replace(/(access_token)(.+?)(?=\&)/, "$1={{request.session.access_token}}");
                                    }
                            } catch(err) {
                                console.log(err);
                            }
                        {% endif %}
                    }
                }

                var map = app.mapPanel.map;
                var layer = app.map.layers.slice(-1)[0];
                var bbox = layer.bbox;
                var crs = layer.crs
                if (bbox != undefined)
                {
                   if (!Array.isArray(bbox) && Object.keys(layer.srs) in bbox) {
                    bbox = bbox[Object.keys(layer.srs)].bbox;
                   }

                   var extent = new OpenLayers.Bounds();

                   if(map.projection != 'EPSG:900913' && crs && crs.properties) {
                       extent.left = bbox[0];
                       extent.right = bbox[1];
                       extent.bottom = bbox[2];
                       extent.top = bbox[3];

                       if (crs.properties != map.projection) {
                           extent = extent.clone().transform(crs.properties, map.projection);
                       }
                   } else {
                       extent = OpenLayers.Bounds.fromArray(bbox);
                   }

                   var zoomToData = function()
                   {
                       map.zoomToExtent(extent, false);
                       app.mapPanel.center = map.center;
                       app.mapPanel.zoom = map.zoom;
                       map.events.unregister('changebaselayer', null, zoomToData);
                   };
                   map.events.register('changebaselayer',null,zoomToData);
                   if(map.baseLayer){
                       map.zoomToExtent(extent, false);
                   }
                }
            },
           'save': function(obj_id) {
               createMapThumbnail(obj_id);
           }
       }
    }, {{ config }});





    /*/TEST
    Ext.namespace("tellme.plugins");
    tellme.plugins.BoxInfo = Ext.extend(gxp.plugins.Tool, {

      ptype: "tellme_boxinfo",

      addOutput: function(config) {
        return tellme.plugins.BoxInfo.superclass.addOutput.call(this, Ext.apply({
          title: "TELLme semantics",
          html: pannello
        }, config));
      }

    });

    Ext.preg(tellme.plugins.BoxInfo.prototype.ptype, tellme.plugins.BoxInfo);



    //////*/
    //end TEST





    Ext.ns("Geosk");
    Geosk.Composer = Ext.extend(GeoNode.Composer, {

        loadConfig: function(config) {
            {% if request.path == '/maps/117/view' or  request.path == '/maps/117/embed' %}
            config.listeners.ready = function(obj_id) {
                setTimeout(function(){
                    var sosUrls = ['http://david.ve.ismar.cnr.it/52nSOSv3_WAR/sos?',
                           'http://nodc.ogs.trieste.it/SOS/sos'
                           //'http://sos.ise.cnr.it/sos?',
                           //'http://sos.ise.cnr.it/biology/sos?',
                           //'http://sos.ise.cnr.it/chemistry/sos?'
                          ]
                    for(var index = 0; index < sosUrls.length; ++index){
                        var sosUrl = sosUrls[index];
                        var sourceConfig = {
                            "config":{
                                "ptype": 'gxp_sossource',
                                "url": sosUrl,
                                "listeners": {
                                    'loaded': function(config){
                                        app.mapPanel.layers.add([config.record]);
                                     }
                                }
                             }
                        };
                        var source = app.addLayerSource(sourceConfig);

                        var layerConfig = {
                            "url": sosUrl,
                            "group": "sos"
                        };

                        layerConfig.source = source.id;
                        sosRecord = source.createLayerRecord(layerConfig);
                        // nei sos vecchi ho dovuto aggiungere anche questa riga di codice
                        //app.mapPanel.layers.add([sosRecord]);
                    }
                });
            }

            // il primo tool e' gxp_layermanager (rendere piu' robusto
            config.tools[0].groups= {
                "sos": "SOS",
                "default": "Overlays", // title can be overridden with overlayNodeText
                "background": {
                    title: "Base Maps", // can be overridden with baseNodeText
                    exclusive: true
                }
            };
            {% endif %}

            config.tools.push(
                {
                    ptype: "gxp_addsos",
                    id: "addsos",
                    outputConfig: {defaults: {autoScroll: true}, width: 320},
                    actionTarget: ["layers.tbar", "layers.contextMenu"],
                    outputTarget: "tree"
                },
                {
                    ptype: "gxp_getsosfeatureinfo"
                }
            );



            //*TELLME TEST

            /*
            var EastPanel = new Ext.Panel({
                region:"east",
                id:"east",
                width:320,
                header:true
            })
            //*/

            /*/
            config.tools.push({
                ptype:"tellme_boxinfo",
                id:"bean",
                outputConfig: {defaults: {autoScroll: true}, width: 320}
                ,outputTarget:"tellme-panel-container"
                //,outputConfig:{layout:"fit",id:"tellmesem",region:"north"}
            })
            //eo tellme test */

            Geosk.Composer.superclass.loadConfig.apply(this, arguments);
        },

        /*
        initPortal: function(){
            this.EastPanel = new Ext.Panel({
                region:"east",
                id:"east",
                width:320,
                split: true,
                collapsible: true,
                collapseMode: "mini",
                hideCollapseTool: true,
                header:false
            });
            this.portalItems=[{
                region:"center",
                layout:"fit",
                items:[this.EastPanel]
            }];
            Geosk.Composer.superclass.initPortal.apply(this,arguments);
        }//*/

    });



    app = new Geosk.Composer(config);

    // insert here the jquery  for enabling tellme semantics management
    app.events.portalready.addListener(function (){

        $( document ).ready(function() {

            $(".li_tellme_keyword").toggleClass("on");

            $(".li_tellme_keyword").on("click", function(){
                if($(this).hasClass("on")){
                    $(this).next().children(".active").click();
                }
                else{
                    $(this).next().children().not(".active").click();
                }
                $(this).toggleClass("on");
            });
            //attr("style","font-weight:bold;");

            $(".conceptToggle").on("click", function() {


                var myid=$(this).prop("id");
                var myidClass="."+myid;

                console.log(myidClass, $(this).hasClass("active"));

                if($(this).hasClass("active")){

                    //disable all layers related to this concept: select the active ones and click them
                    $(myidClass).filter(function(idx){return $(this).prop("checked")}).click();
                }
                else{
                    //enable all layers that are not "checked"
                    $(myidClass).filter(function(idx){return $(this).prop("checked")===false}).click();
                }
                //then toggle the active class on this concept toggle
                $(this).toggleClass("active");


            });


        });

    });

{% endautoescape %}
});


</script>
