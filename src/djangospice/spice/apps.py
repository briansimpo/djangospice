from djangospice.package import AppConfig


class SpiceConfig(AppConfig):
    name = "djangospice.spice"

    def ready(self):
        from djangospice.package.templates import register_template_tags
        register_template_tags()