import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.forms.utils import flatatt
from django.utils.html import format_html, format_html_join

from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel

from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtail.core.fields import RichTextField, StreamField

from wagtail.contrib.table_block.blocks import TableBlock
from wagtailmedia.blocks import VideoChooserBlock

from modelcluster.contrib.taggit import ClusterTaggableManager

from colorful.fields import RGBColorField

from .utils import get_image_model_path


class BlogAbstract(models.Model):
    description = models.CharField(
        verbose_name=_('Description'),
        max_length=255,
        blank=True,
        help_text=_("The blog description that will appear under the title.")
    )
    header_image = models.ForeignKey(
        get_image_model_path(),
        verbose_name=_('Header image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    main_color = RGBColorField(_('Blog Main Color'), default="#4D6AE0")

    display_comments = models.BooleanField(default=False, verbose_name=_('Display comments'))
    display_categories = models.BooleanField(default=True, verbose_name=_('Display categories'))
    display_tags = models.BooleanField(default=True, verbose_name=_('Display tags'))
    display_popular_entries = models.BooleanField(default=True, verbose_name=_('Display popular entries'))
    display_last_entries = models.BooleanField(default=True, verbose_name=_('Display last entries'))
    display_archive = models.BooleanField(default=True, verbose_name=_('Display archive'))

    disqus_api_secret = models.TextField(blank=True)
    disqus_shortname = models.CharField(max_length=128, blank=True)

    num_entries_page = models.IntegerField(default=5, verbose_name=_('Entries per page'))
    num_last_entries = models.IntegerField(default=3, verbose_name=_('Last entries limit'))
    num_popular_entries = models.IntegerField(default=3, verbose_name=_('Popular entries limit'))
    num_tags_entry_header = models.IntegerField(default=5, verbose_name=_('Tags limit entry header'))

    short_feed_description = models.BooleanField(default=True, verbose_name=_('Use short description in feeds'))

    content_panels = [
        FieldPanel('description', classname="full"),
        ImageChooserPanel('header_image'),
        FieldPanel('main_color')
    ]
    settings_panels = [
        MultiFieldPanel([
            FieldPanel('display_categories'),
            FieldPanel('display_tags'),
            FieldPanel('display_popular_entries'),
            FieldPanel('display_last_entries'),
            FieldPanel('display_archive'),
        ], heading=_("Widgets")),
        MultiFieldPanel([
            FieldPanel('num_entries_page'),
            FieldPanel('num_last_entries'),
            FieldPanel('num_popular_entries'),
            FieldPanel('num_tags_entry_header'),
        ], heading=_("Parameters")),
        MultiFieldPanel([
            FieldPanel('display_comments'),
            FieldPanel('disqus_api_secret'),
            FieldPanel('disqus_shortname'),
        ], heading=_("Comments")),
        MultiFieldPanel([
            FieldPanel('short_feed_description'),
        ], heading=_("Feeds")),
    ]

    class Meta:
        abstract = True

class AnimationBlock(VideoChooserBlock):

    def render_basic(self, value, context=None):
        if not value:
            return ''

        tmpl = '''
        <video width="100%" autoplay muted="true" loop="true">
            {0}
            Your browser does not support the video element.
        </video>
        '''

        return format_html(tmpl, format_html_join(
            '\n', '<source{0}>',
            [[flatatt(s) for s in value.sources]]
        ))

class EntryAbstract(models.Model):
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='full title', template='puput/blocks/heading.html')),
        ('paragraph', blocks.RichTextBlock()),
        ('animation', AnimationBlock(icon='media')),
        ('table', TableBlock(template='puput/blocks/table.html')),
        ('image', blocks.StructBlock(
            [
                ('image', ImageChooserBlock()),
                ('caption', blocks.CharBlock(required=False)),
            ],
            template='puput/blocks/captioned_image.html')),
        ('embed', blocks.URLBlock(template='home/partials/embed.html')),
    ])
    tags = ClusterTaggableManager(through='puput.TagEntryPage', blank=True)
    date = models.DateTimeField(verbose_name=_("Post date"), default=datetime.datetime.today)
    header_image = models.ForeignKey(
        get_image_model_path(),
        verbose_name=_('Header image'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    categories = models.ManyToManyField('puput.Category', through='puput.CategoryEntryPage', blank=True)
    excerpt = RichTextField(
        verbose_name=_('excerpt'),
        help_text=_("Short excerpt from or summary of post.")
    )
    num_comments = models.IntegerField(default=0, editable=False)

    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('title', classname="title"),
                ImageChooserPanel('header_image'),
                StreamFieldPanel('body', classname="full"),
                FieldPanel('excerpt', classname="full"),
            ],
            heading=_("Content")
        ),
        MultiFieldPanel(
            [
                FieldPanel('tags'),
                InlinePanel('entry_categories', label=_("Categories")),
                InlinePanel(
                    'related_entrypage_from',
                    label=_("Related Entries"),
                    panels=[PageChooserPanel('entrypage_to')]
                ),
            ],
            heading=_("Metadata")),
    ]

    class Meta:
        abstract = True
