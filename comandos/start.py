import modules.manager as manager
import modules.recovery_system as recovery_system
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from modules.utils import is_admin

def add_user_to_list(user, bot_id):
   print(user)
   print(bot_id)
   users = manager.get_bot_users(bot_id)
   print(users)
   if not user in users:
       users.append(user)
       manager.update_bot_users(bot_id, users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ADICIONAR FLAG PARA INDICAR QUE ESTÁ PROCESSANDO START
    context.user_data['processing_start'] = True
    
    # ADICIONAR TIMESTAMP
    import time
    context.user_data['last_start_time'] = time.time()
    
    config = manager.get_bot_config(context.bot_data['id'])
    user_id = str(update.message.from_user.id)
    bot_id = context.bot_data['id']
    
    # ATUALIZA ÚLTIMA ATIVIDADE DO BOT
    manager.update_bot_last_activity(bot_id)
    
    # ===== MELHORADO: CAPTURA E SALVA PARÂMETROS UTM =====
    tracking_data = {}
    
    # Debug inicial
    print(f"\n[UTM DEBUG] ====== NOVO START ======")
    print(f"[UTM DEBUG] User ID: {user_id}")
    print(f"[UTM DEBUG] Bot ID: {bot_id}")
    print(f"[UTM DEBUG] Args recebidos: {context.args}")
    
    if context.args:  # Se tem parâmetros no /start
        params = context.args[0]
        print(f"[UTM DEBUG] Parâmetros completos: {params}")
        
        # MÉTODO 1: Parse com underscore (formato: start=fbclid-XXX_utm-source-facebook)
        if '_' in params:
            print(f"[UTM DEBUG] Detectado formato com underscore")
            for param in params.split('_'):
                param = param.strip()
                print(f"[UTM DEBUG] Processando parte: {param}")
                
                if param.startswith('fbclid-'):
                    tracking_data['fbclid'] = param.replace('fbclid-', '')
                    print(f"[UTM DEBUG] FBCLID capturado: {tracking_data['fbclid']}")
                elif param.startswith('utm-source-'):
                    tracking_data['utm_source'] = param.replace('utm-source-', '')
                    print(f"[UTM DEBUG] UTM Source capturado: {tracking_data['utm_source']}")
                elif param.startswith('utm-campaign-'):
                    tracking_data['utm_campaign'] = param.replace('utm-campaign-', '')
                    print(f"[UTM DEBUG] UTM Campaign capturado: {tracking_data['utm_campaign']}")
                elif param.startswith('utm-medium-'):
                    tracking_data['utm_medium'] = param.replace('utm-medium-', '')
                    print(f"[UTM DEBUG] UTM Medium capturado: {tracking_data['utm_medium']}")
                elif param.startswith('utm-content-'):
                    tracking_data['utm_content'] = param.replace('utm-content-', '')
                    print(f"[UTM DEBUG] UTM Content capturado: {tracking_data['utm_content']}")
                elif param.startswith('utm-term-'):
                    tracking_data['utm_term'] = param.replace('utm-term-', '')
                    print(f"[UTM DEBUG] UTM Term capturado: {tracking_data['utm_term']}")
                elif param.startswith('sck-'):
                    tracking_data['sck'] = param.replace('sck-', '')
                    print(f"[UTM DEBUG] SCK capturado: {tracking_data['sck']}")
                elif param.startswith('src-'):
                    tracking_data['src'] = param.replace('src-', '')
                    print(f"[UTM DEBUG] SRC capturado: {tracking_data['src']}")
        
        # MÉTODO 2: Tentar parse com hífen (formato: start=fbclid-XXX-utm-source-facebook)
        elif '-' in params:
            print(f"[UTM DEBUG] Detectado formato com hífen")
            # Tenta identificar padrões conhecidos
            import re
            
            # Busca FBCLID
            fbclid_match = re.search(r'fbclid-([A-Za-z0-9_\-]+)', params)
            if fbclid_match:
                tracking_data['fbclid'] = fbclid_match.group(1)
                print(f"[UTM DEBUG] FBCLID capturado: {tracking_data['fbclid']}")
            
            # Busca UTM Source
            source_match = re.search(r'utm-source-([A-Za-z0-9_\-]+)', params)
            if source_match:
                tracking_data['utm_source'] = source_match.group(1)
                print(f"[UTM DEBUG] UTM Source capturado: {tracking_data['utm_source']}")
            
            # Busca UTM Campaign
            campaign_match = re.search(r'utm-campaign-([A-Za-z0-9_\-]+)', params)
            if campaign_match:
                tracking_data['utm_campaign'] = campaign_match.group(1)
                print(f"[UTM DEBUG] UTM Campaign capturado: {tracking_data['utm_campaign']}")
            
            # Busca UTM Medium
            medium_match = re.search(r'utm-medium-([A-Za-z0-9_\-]+)', params)
            if medium_match:
                tracking_data['utm_medium'] = medium_match.group(1)
                print(f"[UTM DEBUG] UTM Medium capturado: {tracking_data['utm_medium']}")
                
        # MÉTODO 3: Formato base64 ou codificado
        else:
            print(f"[UTM DEBUG] Tentando decodificar parâmetro")
            try:
                # Tenta decodificar se estiver em base64
                import base64
                decoded = base64.b64decode(params).decode('utf-8')
                print(f"[UTM DEBUG] Decodificado: {decoded}")
                # Processa o decodificado recursivamente
                # ... adicionar lógica se necessário
            except:
                print(f"[UTM DEBUG] Não é base64, mantendo original")
        
        # IMPORTANTE: Salva no banco se capturou QUALQUER dado
        if tracking_data:
            print(f"[UTM DEBUG] ===== SALVANDO TRACKING =====")
            print(f"[UTM DEBUG] Dados capturados: {tracking_data}")
            
            # Salva no banco
            manager.save_user_tracking(user_id, bot_id, tracking_data)
            
            # Verifica se salvou corretamente
            saved_data = manager.get_user_tracking(user_id, bot_id)
            print(f"[UTM DEBUG] Dados salvos no banco: {saved_data}")
            print(f"[UTM DEBUG] ===== FIM SALVAMENTO =====")
        else:
            print(f"[UTM DEBUG] ⚠️ NENHUM DADO UTM CAPTURADO!")
            
    else:
        print(f"[UTM DEBUG] ⚠️ SEM PARÂMETROS NO START!")
    
    # ===== FIM DA CAPTURA UTM =====
    
    # Adiciona usuário à lista
    add_user_to_list(user_id, bot_id)
    
    # Inicia o sistema de recuperação para este usuário (apenas se não for admin)
    # IMPORTANTE: passa False para não mostrar planos
    if not await is_admin(context, user_id, show_plans_if_not_admin=False):
        recovery_system.start_recovery_for_user(context, user_id, bot_id)
    
    print(config)

    keyboard = [
        [InlineKeyboardButton(config['button'], callback_data='acessar_ofertas')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Verifica tanto 'midia' quanto 'media' para compatibilidade
    media_config = config.get('midia') or config.get('media')
    if media_config:
        if media_config.get('type') == 'photo':
            await context.bot.send_photo(chat_id=user_id, photo=media_config['file'])
        else:
            await context.bot.send_video(chat_id=user_id, video=media_config['file'])

    if config.get('texto1', False):
        await context.bot.send_message(chat_id=update.message.from_user.id, text=config['texto1'])

    await context.bot.send_message(chat_id=update.message.from_user.id, text=config['texto2'], reply_markup=reply_markup)
    
    # LIMPAR FLAG APÓS PROCESSAR
    context.user_data['processing_start'] = False
    
    return ConversationHandler.END