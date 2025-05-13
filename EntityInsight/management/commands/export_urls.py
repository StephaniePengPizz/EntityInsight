# management/commands/export_urls.py
from django.core.management.base import BaseCommand
from django.urls import get_resolver
import json


class Command(BaseCommand):
    help = '导出所有URL路由到JSON文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='url_snapshot.json',
            help='输出文件路径'
        )

    def handle(self, *args, **options):
        urls = self.extract_urls(get_resolver().url_patterns)

        with open(options['output'], 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f'成功导出 {len(urls)} 条URL到 {options["output"]}')
        )

    def extract_urls(self, urlpatterns, base=''):
        urls = []
        for entry in urlpatterns:
            if hasattr(entry, 'url_patterns'):  # URLResolver
                urls += self.extract_urls(
                    entry.url_patterns,
                    base + str(entry.pattern)
                )
            elif hasattr(entry, 'callback'):  # URLPattern
                urls.append({
                    'url': base + str(entry.pattern),
                    'name': entry.name or '',
                    'view': entry.callback.__module__ + '.' + entry.callback.__name__
                })
        return urls