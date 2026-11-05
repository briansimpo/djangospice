from djangospice.package import AppConfig


class SiteConfig(AppConfig):
    name = "djangospice.site"

    def ready(self):
        from djangospice.package.templates import register_template_tags
        register_template_tags()