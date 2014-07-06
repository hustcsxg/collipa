# coding: utf-8

import time
from pony import orm
from ._base import db, SessionMixin, ModelMixin
import models as m
import config

config = config.Config()


class Album(db.Entity, SessionMixin, ModelMixin):
    name = orm.Required(unicode, 400)
    description = orm.Optional(unicode, 1000)
    user_id = orm.Required(int)
    image_count = orm.Required(int, default=0)

    role = orm.Required(unicode, 10, default='album')
    compute_count = orm.Required(int, default=config.reply_compute_count)

    thank_count = orm.Required(int, default=0)
    up_count = orm.Required(int, default=0)
    down_count = orm.Required(int, default=0)
    report_count = orm.Required(int, default=0)
    collect_count = orm.Required(int, default=0)

    floor = orm.Required(int, default=1)

    created_at = orm.Required(int, default=int(time.time()))
    updated_at = orm.Required(int, default=int(time.time()))
    active = orm.Required(int, default=int(time.time()))

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<Album: %s>' % self.id

    @property
    def url(self):
        return '/album/%s' % self.id

    def save(self, category='create', user=None):
        now = int(time.time())
        if category == 'create':
            self.created_at = now
            self.author.album_count += 1

        self.updated_at = now
        self.author.active = now
        self.active = now

        return super(Album, self).save()

    def get_uppers(self, after_date=None, before_date=None):
        if after_date:
            user_ids = orm.select(rv.user_id for rv in m.Up if rv.album_id == self.id and rv.created_at > after_date)
        elif before_date:
            user_ids = orm.select(rv.user_id for rv in m.Up if rv.album_id == self.id and rv.created_at < before_date)
        else:
            user_ids = orm.select(rv.user_id for rv in m.Up if rv.album_id == self.id)
        users = []
        if user_ids:
            user_ids = user_ids.order_by(lambda rv: orm.desc(rv.created_at))

            users = orm.select(rv for rv in m.User if rv.id in user_ids)
        return users

    def get_thankers(self, after_date=None, before_date=None):
        if after_date:
            user_ids = orm.select(rv.user_id for rv in m.Thank if rv.album_id == self.id and rv.created_at > after_date)
        elif before_date:
            user_ids = orm.select(rv.user_id for rv in m.Thank if rv.album_id == self.id and rv.created_at < before_date)
        else:
            user_ids = orm.select(rv.user_id for rv in m.Thank if rv.album_id == self.id)
        users = []
        if user_ids:
            user_ids = user_ids.order_by(lambda rv: orm.desc(rv.created_at))

            users = orm.select(rv for rv in m.User if rv.id in user_ids)
        return users

    def get_images(self, page=1, category='all', order_by='created_at',
                   limit=None):
        if category == 'all':
            images = m.Image.select(lambda rv: rv.topic_id == self.id)
        else:
            if category == 'hot':
                images = m.Image.select(lambda rv: rv.topic_id == self.id)
                limit = 10
                order_by = 'smart'
            elif category == 'author':
                images = orm.select(rv for rv in m.Image if
                                    rv.topic_id == self.id and rv.user_id == self.user_id)
            else:
                images = orm.select(rv for rv in m.Image if rv.topic_id == self.id and rv.role == category)

        if order_by == 'smart':
            images = images.order_by(lambda rv: orm.desc((rv.collect_count +
                                                          rv.thank_count) * 10 +
                                                         (rv.up_count -
                                                          rv.down_count) * 5))
        else:
            images = images.order_by(lambda rv: rv.created_at)

        if limit:
            return images[:limit]
        elif page:
            return images[(page - 1) * config.paged: page * config.paged]
        else:
            return images
