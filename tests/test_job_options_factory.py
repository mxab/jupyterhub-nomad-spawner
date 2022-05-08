from jupyterhub_nomad_spawner.job_options_factory import create_form

from bs4 import BeautifulSoup


def test_create_form():
    datacenters = ["dc1", "dc2"]
    common_images = ["common_image1", "common_image2"]
    csi_plugin_ids = ["csi_plugin_id1", "csi_plugin_id2"]
    memory_limit = 1024
    html = create_form(datacenters, common_images, csi_plugin_ids, memory_limit)

    assert (
        BeautifulSoup(html)
        == BeautifulSoup(
            """

    <div class="form-group">    <label for="image">Image</label>    <input class="form-control" id="image" name="image" required list="common_images"></div><datalist id="common_images">        <option value="common_image1">common_image1</option>        <option value="common_image2">common_image2</option>    </datalist><div class="form-group">    <label for="datacenters">        Datacenters    </label>    <select class="form-control" id="datacenters" name="datacenters" multiple="true" required>                <option value="dc1">dc1</option>                <option value="dc2">dc2</option>            </select></div><div class="form-group">    <label for="memory">Memory</label>    <input class="form-control" type="number" id="memory" min="8" name="memory" value="1024"         max="1024" ></div><div class="radio">    <label>        <input type="radio" name="volume_type" id="volume_type_none" value="" checked>        None    </label></div><div class="radio">    <label>        <input type="radio" name="volume_type" id="volume_type_csi" value="csi">        CSI Volume    </label></div><div class="radio">    <label>        <input type="radio" name="volume_type" id="volume_type_host" value="host">        Host Volume    </label></div><div class="form-group host-volume">    <label for="volume_source">Volume Source</label>    <input class="form-control" id="volume_source" name="volume_source" value="jupyter"></div><div class="form-group csi-volume">    <label for="volume_csi_plugin_id">Volume CSI Plugin ID</label>    <select class="form-control" id="volume_csi_plugin_id" name="volume_csi_plugin_id">                <option value="csi_plugin_id1">csi_plugin_id1</option>                <option value="csi_plugin_id2">csi_plugin_id2</option>            </select></div><div class="form-group volume-destination">    <label for="volume_destination">Volume Destination</label>    <input class="form-control" id="volume_destination" name="volume_destination" value="/home/jovyan/work"></div><script>+(function () {\tjQuery(function($){        function handleType(type){            $(".host-volume").toggle(type == "host")            $(".csi-volume").toggle(type == "csi")            $(".volume-destination").toggle(!!type)            $(".csi-volume :input").prop("disable",type == "host")            $(".host-volume :input").prop("disable", type == "host")            $(".volume-destination :input").prop("disable", !type)        }        $("input[name=volume_type]").on("change", function(){            var type = $(this).val();            handleType(type)        });        var type = $("input[name=volume_type]").val();        handleType(type);    });}());</script>
    """
        ).contents
    )
