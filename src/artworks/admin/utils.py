import json

from django.templatetags.static import static
from django.utils.html import format_html


def external_metadata_html(external_metadata):
    value = json.dumps(external_metadata, indent=2, ensure_ascii=False)
    style = static('highlight/styles/intellij-light.min.css')
    js = static('highlight/highlight.min.js')

    return format_html(
        '<pre style="max-height:300px"><code class="language-json">{}</code></pre>'
        '<link rel="stylesheet" href="{}">'
        '<script src="{}"></script>'
        '<script>hljs.highlightAll();</script>',
        value,
        style,
        js,
    )
