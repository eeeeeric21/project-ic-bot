#!/usr/bin/env python3
"""
Voice Service for Project IC
Handles both Speech-to-Text (ASR) and Text-to-Speech (TTS).

Supports:
- MERaLiON ASR for transcription
- Multiple TTS providers (OpenAI, ElevenLabs, Google, Edge TTS)
"""

import os
import json
import asyncio
import base64
import aiohttp
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum


class TTSProvider(Enum):
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    GOOGLE = "google"
    EDGE = "edge"  # Free, no API key needed


@dataclass
class VoiceConfig:
    """Voice configuration for TTS."""
    provider: TTSProvider
    voice_id: str
    language: str = "en"
    speed: float = 0.9  # Slower for elderly users


# Recommended voices for elderly care
ELDERLY_VOICE_CONFIGS = {
    TTSProvider.OPENAI: VoiceConfig(
        provider=TTSProvider.OPENAI,
        voice_id="nova",  # Warm, friendly female voice
        speed=0.85
    ),
    TTSProvider.ELEVENLABS: VoiceConfig(
        provider=TTSProvider.ELEVENLABS,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel - natural, caring
        speed=0.85
    ),
    TTSProvider.EDGE: VoiceConfig(
        provider=TTSProvider.EDGE,
        voice_id="en-US-JennyNeural",  # Natural Microsoft voice
        speed=0.85
    ),
}


class TTSService:
    """Text-to-Speech service with multiple providers."""
    
    def __init__(self, provider: TTSProvider = TTSProvider.EDGE):
        self.provider = provider
        self.config = ELDERLY_VOICE_CONFIGS.get(provider)
        self.api_keys = {
            "openai": os.environ.get("OPENAI_API_KEY"),
            "elevenlabs": os.environ.get("ELEVENLABS_API_KEY"),
            "google": os.environ.get("GOOGLE_TTS_KEY"),
        }
    
    async def synthesize(self, text: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            output_path: Optional path to save audio file
            
        Returns:
            Audio bytes if successful, None otherwise
        """
        if self.provider == TTSProvider.EDGE:
            return await self._synthesize_edge(text, output_path)
        elif self.provider == TTSProvider.OPENAI:
            return await self._synthesize_openai(text, output_path)
        elif self.provider == TTSProvider.ELEVENLABS:
            return await self._synthesize_elevenlabs(text, output_path)
        else:
            print(f"TTS provider {self.provider} not implemented")
            return None
    
    async def _synthesize_edge(self, text: str, output_path: Optional[str]) -> Optional[bytes]:
        """Use Edge TTS (free, no API key needed)."""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(
                text,
                self.config.voice_id,
                rate=f"-{int((1 - self.config.speed) * 100)}%"  # Slower
            )
            
            if output_path:
                await communicate.save(output_path)
                with open(output_path, 'rb') as f:
                    return f.read()
            else:
                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    await communicate.save(tmp.name)
                    with open(tmp.name, 'rb') as f:
                        audio = f.read()
                    os.unlink(tmp.name)
                    return audio
                    
        except ImportError:
            print("edge-tts not installed. Run: pip install edge-tts")
            return None
        except Exception as e:
            print(f"Edge TTS error: {e}")
            return None
    
    async def _synthesize_openai(self, text: str, output_path: Optional[str]) -> Optional[bytes]:
        """Use OpenAI TTS API."""
        api_key = self.api_keys.get("openai")
        if not api_key:
            print("OPENAI_API_KEY not set")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.openai.com/v1/audio/speech"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "tts-1",
                    "input": text,
                    "voice": self.config.voice_id,
                    "speed": self.config.speed
                }
                
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        audio = await resp.read()
                        if output_path:
                            with open(output_path, 'wb') as f:
                                f.write(audio)
                        return audio
                    else:
                        print(f"OpenAI TTS error: {resp.status}")
                        return None
                        
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
            return None
    
    async def _synthesize_elevenlabs(self, text: str, output_path: Optional[str]) -> Optional[bytes]:
        """Use ElevenLabs TTS API."""
        api_key = self.api_keys.get("elevenlabs")
        if not api_key:
            print("ELEVENLABS_API_KEY not set")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config.voice_id}"
                headers = {
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        audio = await resp.read()
                        if output_path:
                            with open(output_path, 'wb') as f:
                                f.write(audio)
                        return audio
                    else:
                        print(f"ElevenLabs TTS error: {resp.status}")
                        return None
                        
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None


class ASRService:
    """Automatic Speech Recognition service with multiple providers."""
    
    def __init__(self):
        self.api_url = os.environ.get("MERALION_API_URL", "")
        self.api_key = os.environ.get("MERALION_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("MERALION_MODEL", "MERaLiON/MERaLiON-3-10B")
    
    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        """
        Transcribe audio to text.
        
        Tries MERaLiON ASR first, falls back to OpenAI Whisper.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (en, zh, ms, ta)
            
        Returns:
            Transcribed text
        """
        # Try MERaLiON ASR first (uses same endpoint with audio content)
        if self.api_url and self.api_key:
            result = await self._transcribe_meralion(audio_data, language)
            if result:
                return result
        
        # Fallback to OpenAI Whisper
        if self.openai_key:
            result = await self._transcribe_openai(audio_data, language)
            if result:
                return result
        
        print("⚠️ No ASR service available. Set MERALION_API_KEY for voice input.")
        return ""
    
    async def _transcribe_meralion(self, audio_data: bytes, language: str = "en") -> str:
        """Use MERaLiON for transcription via chat completions with audio."""
        try:
            # Base64 encode audio
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Determine audio format (Telegram sends OGG, MERaLiON might expect WAV)
            # Try with OGG first, then WAV if needed
            audio_formats = [
                ("audio/ogg", "ogg"),  # Telegram format
                ("audio/wav", "wav"),  # Standard format
                ("audio/mp3", "mp3"),
            ]
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                for content_type, ext in audio_formats:
                    payload = {
                        "model": self.model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Transcribe this audio. Only output the transcription, nothing else."},
                                {"type": "audio_url", "audio_url": {"url": f"data:{content_type};base64,{audio_base64}"}},
                            ],
                        }],
                        "max_tokens": 500
                    }
                    
                    try:
                        async with session.post(url, headers=headers, json=payload,
                                              timeout=aiohttp.ClientTimeout(total=60)) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                if text:
                                    print(f"✅ MERaLiON ASR: {text[:50]}...")
                                    return text
                            else:
                                error = await resp.text()
                                print(f"MERaLiON ASR error ({content_type}): {resp.status}")
                    except Exception as e:
                        print(f"MERaLiON ASR exception ({content_type}): {e}")
                        continue
                
                print("MERaLiON ASR: No supported audio format worked")
                return ""
                
        except Exception as e:
            print(f"MERaLiON ASR error: {e}")
            return ""
    
    async def _transcribe_openai(self, audio_data: bytes, language: str = "en") -> str:
        """Use OpenAI Whisper API for transcription."""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.openai.com/v1/audio/transcriptions"
                headers = {
                    "Authorization": f"Bearer {self.openai_key}",
                }
                
                # Build multipart form data
                data = aiohttp.FormData()
                data.add_field('file', audio_data, filename='audio.ogg', content_type='audio/ogg')
                data.add_field('model', 'whisper-1')
                data.add_field('language', language)
                
                async with session.post(url, headers=headers, data=data,
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        text = result.get("text", "")
                        print(f"✅ Whisper transcription: {text[:50]}...")
                        return text
                    else:
                        error = await resp.text()
                        print(f"Whisper error: {resp.status} - {error[:100]}")
                        return ""
                        
        except Exception as e:
            print(f"OpenAI Whisper error: {e}")
            return ""

    def _transcribe_meralion_old(self, audio_data: bytes, language: str = "en") -> str:
        """Old MERaLiON ASR method - kept for reference."""
        pass  # Replaced with new implementation above


class VoiceConversationManager:
    """
    Manages complete voice conversation flow.
    
    Usage:
        manager = VoiceConversationManager()
        
        # User speaks
        user_text = await manager.transcribe(audio_bytes)
        
        # AI responds
        ai_response = await get_ai_response(user_text)
        
        # Speak back
        audio = await manager.speak(ai_response)
        # Send audio to user
    """
    
    def __init__(self, 
                 tts_provider: TTSProvider = TTSProvider.EDGE,
                 use_asr: bool = True):
        self.tts = TTSService(tts_provider)
        self.asr = ASRService() if use_asr else None
        
        # Conversation state
        self.conversation_history = []
    
    async def listen(self, audio_data: bytes, language: str = "en") -> str:
        """
        Listen to audio and return transcribed text.
        """
        if not self.asr:
            raise RuntimeError("ASR not enabled")
        
        return await self.asr.transcribe(audio_data, language)
    
    async def speak(self, text: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Convert response text to speech audio.
        """
        return await self.tts.synthesize(text, output_path)
    
    async def conversation_turn(self, 
                                 user_audio: bytes,
                                 ai_responder,  # Function that takes text, returns AI response
                                 language: str = "en") -> Dict:
        """
        Complete conversation turn: Listen → Think → Speak
        
        Args:
            user_audio: User's voice input
            ai_responder: Async function that processes text and returns response
            language: Language code
            
        Returns:
            {
                "transcription": str,
                "ai_response": str,
                "response_audio": bytes
            }
        """
        # 1. Listen
        user_text = await self.listen(user_audio, language)
        
        # 2. Think (get AI response)
        ai_response = await ai_responder(user_text)
        
        # 3. Speak
        response_audio = await self.speak(ai_response)
        
        # Track history
        self.conversation_history.append({
            "user": user_text,
            "assistant": ai_response
        })
        
        return {
            "transcription": user_text,
            "ai_response": ai_response,
            "response_audio": response_audio
        }


# CLI Test
async def test_tts():
    """Test TTS functionality."""
    print("=" * 60)
    print("🗣️ Testing Text-to-Speech")
    print("=" * 60)
    
    # Test with Edge TTS (free, no API key)
    tts = TTSService(TTSProvider.EDGE)
    
    test_text = "Good morning, Uncle Tan! How are you feeling today, ah?"
    
    print(f"\nText: {test_text}")
    print("Generating speech...")
    
    output_path = "/tmp/test_voice.mp3"
    audio = await tts.synthesize(test_text, output_path)
    
    if audio:
        print(f"✅ Audio saved to: {output_path}")
        print(f"   Size: {len(audio)} bytes")
        print("\nPlay with: afplay /tmp/test_voice.mp3")
    else:
        print("❌ TTS failed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_tts())
    else:
        print("Voice Service for Project IC")
        print("\nUsage:")
        print("  python voice_service.py test  - Test TTS")
