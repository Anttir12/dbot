from rest_framework import renderers


class AudioOGGRenderer(renderers.BaseRenderer):
    media_type = 'audio/ogg'
    format = 'ogg'
    charset = None
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data