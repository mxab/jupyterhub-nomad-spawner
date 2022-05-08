from typing import List, Optional
from jinja2 import Environment, PackageLoader, select_autoescape


def create_form(
    datacenters: List[str],
    common_images: List[str],
    csi_plugin_ids: Optional[List[str]],
    memory_limit: Optional[int] = None,
) -> str:

    env = Environment(
        loader=PackageLoader("jupyterhub_nomad_spawner"), autoescape=select_autoescape()
    )

    template = env.get_template("form.html.j2")
    html = template.render(
        csi_plugin_ids=csi_plugin_ids,
        common_images=common_images,
        datacenters=datacenters,
        memory_limit=memory_limit,
    )

    return html
