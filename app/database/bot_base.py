import os
import json
import asyncio
from datetime import datetime
from difflib import SequenceMatcher
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or Key is missing in .env file")

supabase: Client = create_client(url, key)

# ==================== ADD FUNCTIONS ====================

def add_user_base_sync(user_id, username, lang="uz", is_admin=False, is_staff=False):
    data = {
        "user_id": user_id,
        "username": username,
        "lang": lang,
        "is_admin": is_admin,
        "is_staff": is_staff,
        "is_anipass": None,
        "is_lux": None
    }
    try:
        supabase.table("users").insert(data).execute()
        update_statistics_user_count_base_sync()
    except Exception as e:
        print(f"Error adding user: {e}")

async def add_user_base(user_id, username, lang="uz", is_admin=False, is_staff=False):
    return await asyncio.to_thread(add_user_base_sync, user_id, username, lang, is_admin, is_staff)

def add_media_base_sync(trailer_id, name, genre, tag, dub, series=0, status="loading", views=0, msg_id=0, type="anime"):
    data = {
        "trailer_id": trailer_id,
        "name": name,
        "genre": genre,
        "tag": tag,
        "dub": dub,
        "series": series,
        "status": status,
        "views": views,
        "msg_id": msg_id,
        "type": type,
        "is_vip": False
    }
    
    response = supabase.table("media").insert(data).execute()
    
    if type == "anime":
        current_stats = get_statistics_base_sync()
        new_count = current_stats.get("anime_count", 0) + 1
        supabase.table("statistics").update({"anime_count": new_count}).eq("bot_name", "bot").execute()
    else:
        current_stats = get_statistics_base_sync()
        new_count = current_stats.get("drama_count", 0) + 1
        supabase.table("statistics").update({"drama_count": new_count}).eq("bot_name", "bot").execute()

    if response.data:
        return response.data[0]['media_id']
    return None

async def add_media_base(trailer_id, name, genre, tag, dub, series=0, status="loading", views=0, msg_id=0, type="anime"):
    return await asyncio.to_thread(add_media_base_sync, trailer_id, name, genre, tag, dub, series, status, views, msg_id, type)

def add_episode_base_sync(which_media, episode_id, episode_num, msg_id):
    data = {
        "which_media": which_media,
        "episode_id": episode_id,
        "episode_num": episode_num,
        "msg_id": msg_id
    }
    response = supabase.table("episodes").insert(data).execute()
    if response.data:
        return response.data[0]['id']
    return None

async def add_episode_base(which_media, episode_id, episode_num, msg_id):
    return await asyncio.to_thread(add_episode_base_sync, which_media, episode_id, episode_num, msg_id)

def add_sponsor_base_sync(channel_id, channel_name, channel_link, type, user_limit):
    data = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_link": channel_link,
        "type": type,
        "user_limit": user_limit
    }
    response = supabase.table("sponsors").insert(data).execute()
    if response.data:
        return response.data[0]['id']
    return None

async def add_sponsor_base(channel_id, channel_name, channel_link, type, user_limit):
    return await asyncio.to_thread(add_sponsor_base_sync, channel_id, channel_name, channel_link, type, user_limit)

def add_sponsor_request_base_sync(channel_id, user_id):
    data_exists = get_sponsor_request_base_sync(channel_id, user_id)
    if not data_exists:
        supabase.table("sponsor_request").insert({"chat_id": channel_id, "user_id": user_id}).execute()
        
        sponsor = get_single_sponsors_base_sync(channel_id)
        if sponsor:
            sponsor_limit = sponsor['user_limit'] - 1
            
            if sponsor_limit == 0:
                delete_sponsor_base_sync(channel_id)
            else:
                update_sponsor_limit_count_minus_base_sync(channel_id)

async def add_sponsor_request_base(channel_id, user_id):
    return await asyncio.to_thread(add_sponsor_request_base_sync, channel_id, user_id)

# ==================== GET FUNCTIONS ====================

def get_sponsor_request_base_sync(channel_id, user_id):
    response = supabase.table("sponsor_request").select("*").eq("user_id", user_id).eq("chat_id", channel_id).execute()
    if response.data:
        return response.data[0]
    return None

async def get_sponsor_request_base(channel_id, user_id):
    return await asyncio.to_thread(get_sponsor_request_base_sync, channel_id, user_id)

def get_user_base_sync(user_id):
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    return None

async def get_user_base(user_id):
    return await asyncio.to_thread(get_user_base_sync, user_id)

def get_all_user_id_base_sync():
    response = supabase.table("users").select("user_id").execute()
    return response.data 

async def get_all_user_id_base():
    return await asyncio.to_thread(get_all_user_id_base_sync)

def get_all_ongoing_media_base_sync():
    response = supabase.table("media").select("*").eq("status", "loading").execute()
    return response.data

async def get_all_ongoing_media_base():
    return await asyncio.to_thread(get_all_ongoing_media_base_sync)

def get_all_media_base_sync(type):
    response = supabase.table("media").select("*").eq("type", type).execute()
    return response.data

async def get_all_media_base(type):
    return await asyncio.to_thread(get_all_media_base_sync, type)

def search_media_base_sync(name, type):
    if type == "any":
        response = supabase.table("media").select("*").ilike("name", f"%{name}%").execute()
    else:
        response = supabase.table("media").select("*").ilike("name", f"%{name}%").eq("type", type).execute()
    
    data = response.data
    
    if not data:
        if type == "any":
            all_media = supabase.table("media").select("*").execute().data
        else:
            all_media = supabase.table("media").select("*").eq("type", type).execute().data
            
        def similar(a, b):
            return SequenceMatcher(None, a, b).ratio()

        new_data = []
        for i in all_media:
            similarity = similar(i["name"], name)
            if similarity >= 0.4:
                new_data.append([similarity, i])
            else:
                try:
                    if i["tag"]:
                        tags = i["tag"].split(",")
                        for tag in tags:
                            tag_similarity = similar(tag, name)
                            if tag_similarity >= 0.5:
                                new_data.append([tag_similarity, i])
                                break
                except KeyError:
                    pass
        
        new_data.sort(reverse=True, key=lambda x: x[0])
        return [i[1] for i in new_data]

    else:
        return data

async def search_media_base(name, type):
    return await asyncio.to_thread(search_media_base_sync, name, type)

def get_media_base_sync(media_id):
    response = supabase.table("media").select("*").eq("media_id", media_id).execute()
    if response.data:
        return response.data[0]
    return [] 

async def get_media_base(media_id):
    return await asyncio.to_thread(get_media_base_sync, media_id)

def get_media_episodes_base_sync(media_id):
    response = supabase.table("episodes").select("*").eq("which_media", media_id).order("episode_num", desc=False).execute()
    return response.data

async def get_media_episodes_base(media_id):
    return await asyncio.to_thread(get_media_episodes_base_sync, media_id)

def get_statistics_base_sync():
    response = supabase.table("statistics").select("*").eq("bot_name", "bot").execute()
    if response.data:
        return response.data[0]
    return {}

async def get_statistics_base():
    return await asyncio.to_thread(get_statistics_base_sync)

def get_all_sponsors_base_sync():
    response = supabase.table("sponsors").select("*").execute()
    return response.data

async def get_all_sponsors_base():
    return await asyncio.to_thread(get_all_sponsors_base_sync)

def get_single_sponsors_base_sync(channel_id):
    response = supabase.table("sponsors").select("*").eq("channel_id", channel_id).execute()
    if response.data:
        return response.data[0]
    return []

async def get_single_sponsors_base(channel_id):
    return await asyncio.to_thread(get_single_sponsors_base_sync, channel_id)

def get_all_staff_base_sync():
    response = supabase.table("users").select("*").eq("is_staff", True).execute()
    return response.data

async def get_all_staff_base():
    return await asyncio.to_thread(get_all_staff_base_sync)

# ==================== UPDATE FUNCTIONS ====================

def update_statistics_user_count_base_sync():
    stats = get_statistics_base_sync()
    if stats:
        new_count = stats.get('users_count', 0) + 1
        supabase.table("statistics").update({"users_count": new_count}).eq("bot_name", "bot").execute()

async def update_statistics_user_count_base():
    return await asyncio.to_thread(update_statistics_user_count_base_sync)

def update_media_episodes_count_plus_base_sync(media_id):
    media = get_media_base_sync(media_id)
    if media:
        new_series = media.get('series', 0) + 1
        supabase.table("media").update({"series": new_series}).eq("media_id", media_id).execute()

async def update_media_episodes_count_plus_base(media_id):
    return await asyncio.to_thread(update_media_episodes_count_plus_base_sync, media_id)

def update_media_episodes_count_minus_base_sync(media_id):
    media = get_media_base_sync(media_id)
    if media:
        new_series = media.get('series', 0) - 1
        supabase.table("media").update({"series": new_series}).eq("media_id", media_id).execute()

async def update_media_episodes_count_minus_base(media_id):
    return await asyncio.to_thread(update_media_episodes_count_minus_base_sync, media_id)

def update_media_name_base_sync(media_id, name):
    supabase.table("media").update({"name": name}).eq("media_id", media_id).execute()

async def update_media_name_base(media_id, name):
    return await asyncio.to_thread(update_media_name_base_sync, media_id, name)

def update_media_genre_base_sync(media_id, genre):
    supabase.table("media").update({"genre": genre}).eq("media_id", media_id).execute()

async def update_media_genre_base(media_id, genre):
    return await asyncio.to_thread(update_media_genre_base_sync, media_id, genre)

def update_media_tag_base_sync(media_id, tag):
    supabase.table("media").update({"tag": tag}).eq("media_id", media_id).execute()

async def update_media_tag_base(media_id, tag):
    return await asyncio.to_thread(update_media_tag_base_sync, media_id, tag)

def update_media_dub_base_sync(media_id, dub):
    supabase.table("media").update({"dub": dub}).eq("media_id", media_id).execute()

async def update_media_dub_base(media_id, dub):
    return await asyncio.to_thread(update_media_dub_base_sync, media_id, dub)

def update_media_vip_base_sync(media_id, is_vip):
    supabase.table("media").update({"is_vip": is_vip}).eq("media_id", media_id).execute()

async def update_media_vip_base(media_id, is_vip):
    return await asyncio.to_thread(update_media_vip_base_sync, media_id, is_vip)

def update_media_status_base_sync(media_id, status):
    supabase.table("media").update({"status": status}).eq("media_id", media_id).execute()

async def update_media_status_base(media_id, status):
    return await asyncio.to_thread(update_media_status_base_sync, media_id, status)

def update_episode_base_sync(media_id, episode_num, episode_id):
    supabase.table("episodes").update({"episode_id": episode_id}).eq("which_media", media_id).eq("episode_num", episode_num).execute()

async def update_episode_base(media_id, episode_num, episode_id):
    return await asyncio.to_thread(update_episode_base_sync, media_id, episode_num, episode_id)

def update_user_staff_base_sync(user_id, value):
    is_staff = True if value else False
    supabase.table("users").update({"is_staff": is_staff}).eq("user_id", user_id).execute()

async def update_user_staff_base(user_id, value):
    return await asyncio.to_thread(update_user_staff_base_sync, user_id, value)

def update_user_admin_base_sync(user_id, value):
    is_admin = True if value else False
    supabase.table("users").update({"is_admin": is_admin}).eq("user_id", user_id).execute()

async def update_user_admin_base(user_id, value):
    return await asyncio.to_thread(update_user_admin_base_sync, user_id, value)

def update_anipass_data_base_sync():
    current_date = datetime.now().isoformat()
    response = supabase.table("users").select("user_id").lt("is_anipass", current_date).not_.is_("is_anipass", "null").execute()
    data = response.data
    
    if data:
        supabase.table("users").update({"is_anipass": None}).lt("is_anipass", current_date).execute()
        
    return data

async def update_anipass_data_base():
    return await asyncio.to_thread(update_anipass_data_base_sync)

def update_lux_data_base_sync():
    current_date = datetime.now().isoformat()
    response = supabase.table("users").select("user_id").lt("is_lux", current_date).not_.is_("is_lux", "null").execute()
    data = response.data
    
    if data:
        supabase.table("users").update({"is_lux": None}).lt("is_lux", current_date).execute()
        
    return data

async def update_lux_data_base():
    return await asyncio.to_thread(update_lux_data_base_sync)

def update_sponsor_limit_count_minus_base_sync(channel_id):
    sponsor = get_single_sponsors_base_sync(channel_id)
    if sponsor:
        new_limit = sponsor.get('user_limit', 0) - 1
        supabase.table("sponsors").update({"user_limit": new_limit}).eq("channel_id", channel_id).execute()

async def update_sponsor_limit_count_minus_base(channel_id):
    return await asyncio.to_thread(update_sponsor_limit_count_minus_base_sync, channel_id)

# ==================== DELETE FUNCTIONS ====================

def delete_episode_base_sync(media_id, episode_num):
    supabase.table("episodes").delete().eq("which_media", media_id).eq("episode_num", episode_num).execute()

async def delete_episode_base(media_id, episode_num):
    return await asyncio.to_thread(delete_episode_base_sync, media_id, episode_num)

def delete_sponsor_base_sync(channel_id):
    supabase.table("sponsors").delete().eq("channel_id", channel_id).execute()
    supabase.table("sponsor_request").delete().eq("chat_id", channel_id).execute()

async def delete_sponsor_base(channel_id):
    return await asyncio.to_thread(delete_sponsor_base_sync, channel_id)

def delete_media_base_sync(media_id):
    """Delete media and all its episodes"""
    supabase.table("episodes").delete().eq("which_media", media_id).execute()
    supabase.table("media").delete().eq("media_id", media_id).execute()

async def delete_media_base(media_id):
    return await asyncio.to_thread(delete_media_base_sync, media_id)

