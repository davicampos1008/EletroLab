from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # É ESTA PARTE AQUI QUE O BANCO DE DADOS ESTÁ SENTINDO FALTA:
    TIPO_CHOICES = (
        ('eletronica', 'Eletrônica e Hardware'),
        ('programacao', 'Programação e Software'),
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='eletronica')

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Armazena as peças e componentes retirados ou salvos no estoque."""
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    quantidade = models.IntegerField(default=1)
    foto = models.ImageField(upload_to='inventory_parts/', blank=True, null=True)
    origem_equipamento = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.quantidade}x)"


class UserTool(models.Model):
    """Controla quais ferramentas e equipamentos o usuário POSSUI ou NÃO POSSUI."""
    nome_ferramenta = models.CharField(max_length=255, unique=True)
    disponivel = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Possui" if self.disponivel else "Não Possui"
        return f"{self.nome_ferramenta} - {status}"