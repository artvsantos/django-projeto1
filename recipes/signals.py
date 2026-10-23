"""Apaga do armazenamento a foto que a receita deixou de usar.

O Django apaga a linha do banco, mas nunca o arquivo. Sem isto, toda
receita apagada ou foto trocada deixava a imagem antiga no Cloudinary,
acessível por quem tivesse o endereço.

O arquivo só sai depois que o banco confirma (transaction.on_commit): se
o save falhar no meio, a receita continua apontando para uma foto que
ainda existe.
"""
import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from recipes.models import Recipe

logger = logging.getLogger(__name__)


def _delete_file_after_commit(field_file):
    if not field_file:
        return
    storage, name = field_file.storage, field_file.name

    def delete():
        # No Cloudinary isto é uma chamada de rede. Se falhar, o banco já
        # foi gravado: melhor um arquivo órfão no log do que um erro 500.
        try:
            storage.delete(name)
        except Exception:
            logger.warning('Não consegui apagar a foto %s', name, exc_info=True)

    transaction.on_commit(delete)


@receiver(pre_save, sender=Recipe)
def remember_old_cover(sender, instance, **kwargs):
    instance._old_cover = None
    if instance.pk is None:
        return
    old = Recipe.objects.filter(pk=instance.pk).only('cover').first()
    if old is not None:
        instance._old_cover = old.cover


@receiver(post_save, sender=Recipe)
def delete_replaced_cover(sender, instance, **kwargs):
    old_cover = getattr(instance, '_old_cover', None)
    if old_cover and old_cover.name != instance.cover.name:
        _delete_file_after_commit(old_cover)


@receiver(post_delete, sender=Recipe)
def delete_cover_with_recipe(sender, instance, **kwargs):
    _delete_file_after_commit(instance.cover)
