import sdl2
import sdl2.ext
import ctypes
import numpy as np
import os
import sys
from .util.log import logger

class Screen:
    def __init__(self, title: str, width: int, height: int):
        self.title = title
        self.width = width
        self.height = height
        self.window = None
        self.renderer = None
        self.texture = None
        self.opened = False
        self.on_sdl_event_callback = None
        # Área exata onde o vídeo é renderizado (com letterboxing)
        self._video_rect = (0, 0, width, height)
        
        # Get screen dimensions for smart scaling
        self.screen_w = 1920
        self.screen_h = 1080
        
        self.loading_texture = None
        self.loading_font = None

    def _set_window_icon(self):
        try:
            import sdl2.sdlimage as sdlimage
            # Find the icon path (handles both normal and EXE mode)
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(base_dir, "images", "furious-mirror.png")
            if not os.path.exists(icon_path):
                # Fallback to portables path
                icon_path = os.path.join(base_dir, "portables", "images", "furious-mirror.png")
                
            if os.path.exists(icon_path):
                surface = sdlimage.IMG_Load(icon_path.encode())
                if surface:
                    sdl2.SDL_SetWindowIcon(self.window, surface)
                    sdl2.SDL_FreeSurface(surface)
        except:
            pass

    def set_on_sdl_event_callback(self, callback):
        self.on_sdl_event_callback = callback

    def init_sdl(self):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO) != 0:
            logger.error(f"SDL_Init Error: {sdl2.SDL_GetError()}")
            return False
            
        try:
            import sdl2.sdlttf as sdlttf
            sdlttf.TTF_Init()
        except Exception as e:
            logger.error(f"TTF_Init Error: {e}")
        
        # Get actual desktop display mode for limits
        mode = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetCurrentDisplayMode(0, ctypes.byref(mode))
        self.screen_w = mode.w
        self.screen_h = mode.h
        logger.info(f"Monitor detected: {self.screen_w}x{self.screen_h}")

        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"1")
        
        self.window = sdl2.SDL_CreateWindow(
            self.title.encode("utf-8"),
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.width,
            self.height,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI
        )
        
        if not self.window:
            logger.error(f"SDL_CreateWindow Error: {sdl2.SDL_GetError()}")
            return False
            
        self._set_window_icon()
        
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED
        )
        
        if not self.renderer:
            logger.error(f"SDL_CreateRenderer Error: {sdl2.SDL_GetError()}")
            return False
            
        self.opened = True
        return True

    def update_frame(self, frame):
        if not self.opened:
            return
            
        w, h = frame.width, frame.height
        
        # Check for resolution change (rotation)
        if not self.texture or self.width != w or self.height != h:
            logger.info(f"Resolution changed: {w}x{h}")
            if self.texture:
                sdl2.SDL_DestroyTexture(self.texture)
            self.texture = sdl2.SDL_CreateTexture(
                self.renderer,
                sdl2.SDL_PIXELFORMAT_IYUV,
                sdl2.SDL_TEXTUREACCESS_STREAMING,
                w, h
            )
            self.width = w
            self.height = h
            
            # Smart Scaling: Never larger than 80% of monitor
            max_w = int(self.screen_w * 0.8)
            max_h = int(self.screen_h * 0.8)
            
            scale = 1.0
            if w > max_w or h > max_h:
                scale = min(max_w / w, max_h / h)
            
            win_w = int(w * scale)
            win_h = int(h * scale)
            
            # Resize window
            sdl2.SDL_SetWindowSize(self.window, win_w, win_h)
            
            # Center window after resize
            sdl2.SDL_SetWindowPosition(self.window, sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED)
            
            sdl2.SDL_SetWindowTitle(self.window, f"Furious Mirror ({w}x{h})".encode("utf-8"))

        # Update YUV texture
        sdl2.SDL_UpdateYUVTexture(
            self.texture, None,
            ctypes.cast(frame.planes[0].buffer_ptr, ctypes.POINTER(ctypes.c_ubyte)), frame.planes[0].line_size,
            ctypes.cast(frame.planes[1].buffer_ptr, ctypes.POINTER(ctypes.c_ubyte)), frame.planes[1].line_size,
            ctypes.cast(frame.planes[2].buffer_ptr, ctypes.POINTER(ctypes.c_ubyte)), frame.planes[2].line_size
        )
        
        sdl2.SDL_RenderClear(self.renderer)
        # Preserve aspect ratio by using destination rect based on window size
        win_w, win_h = self.get_window_size()
        
        # Calculate aspect ratio scaling for rendering
        scale = min(win_w / self.width, win_h / self.height)
        dst_w = int(self.width * scale)
        dst_h = int(self.height * scale)
        dst_x = (win_w - dst_w) // 2
        dst_y = (win_h - dst_h) // 2
        
        # Salva a area real do video (usada para mapeamento de cliques)
        self._video_rect = (dst_x, dst_y, dst_w, dst_h)
        
        dest_rect = sdl2.SDL_Rect(dst_x, dst_y, dst_w, dst_h)
        
        sdl2.SDL_RenderCopy(self.renderer, self.texture, None, dest_rect)
        sdl2.SDL_RenderPresent(self.renderer)

    def _init_loading_assets(self):
        try:
            import sdl2.sdlttf as sdlttf
            import sdl2.sdlimage as sdlimage
            
            if not self.loading_font:
                font_path = b"C:\\Windows\\Fonts\\segoeui.ttf"
                if os.path.exists(font_path):
                    self.loading_font = sdlttf.TTF_OpenFont(font_path, 20)
            
            if not self.loading_texture:
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                icon_path = os.path.join(base_dir, "images", "furious-mirror.png")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(base_dir, "portables", "images", "furious-mirror.png")
                    
                if os.path.exists(icon_path):
                    surface = sdlimage.IMG_Load(icon_path.encode())
                    if surface:
                        self.loading_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
                        sdl2.SDL_FreeSurface(surface)
        except Exception as e:
            logger.error(f"Erro ao carregar assets de loading: {e}")

    def draw_loading_screen(self, frame_counter=0, text="Iniciando..."):
        if not self.opened:
            return
            
        if not hasattr(self, '_loading_assets_loaded'):
            self._init_loading_assets()
            self._loading_assets_loaded = True
            
        # Cor de fundo premium Cyberpunk (Deep Dark Purple/Black)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 8, 4, 15, 255)
        sdl2.SDL_RenderClear(self.renderer)
        
        win_w, win_h = self.get_window_size()
        
        # Animação de respiração
        import math
        scale_pulse = 0.95 + 0.05 * math.sin(frame_counter * 0.1)
        alpha = int(200 + 55 * math.sin(frame_counter * 0.1))
        
        if self.loading_texture:
            sdl2.SDL_SetTextureAlphaMod(self.loading_texture, alpha)
            
            w, h = 256, 256
            dst_w = int(w * scale_pulse)
            dst_h = int(h * scale_pulse)
            dst_x = (win_w - dst_w) // 2
            dst_y = (win_h - dst_h) // 2 - 40
            
            dest_rect = sdl2.SDL_Rect(dst_x, dst_y, dst_w, dst_h)
            sdl2.SDL_RenderCopy(self.renderer, self.loading_texture, None, dest_rect)
            
        if self.loading_font and text:
            import sdl2.sdlttf as sdlttf
            # Cyberpunk Neon Cyan
            color = sdl2.SDL_Color(0, 240, 255, int(alpha))
            text_surface = sdlttf.TTF_RenderUTF8_Blended(self.loading_font, text.encode('utf-8'), color)
            if text_surface:
                text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, text_surface)
                if text_texture:
                    tw, th = text_surface.contents.w, text_surface.contents.h
                    tx = (win_w - tw) // 2
                    ty = (win_h - th) // 2 + 120
                    text_rect = sdl2.SDL_Rect(tx, ty, tw, th)
                    sdl2.SDL_RenderCopy(self.renderer, text_texture, None, text_rect)
                    sdl2.SDL_DestroyTexture(text_texture)
                sdl2.SDL_FreeSurface(text_surface)
            
        sdl2.SDL_RenderPresent(self.renderer)


    def handle_events(self) -> bool:
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_QUIT:
                return False
            
            if self.on_sdl_event_callback:
                self.on_sdl_event_callback(event)
                
        return True

    def get_window_size(self):
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_GetWindowSize(self.window, ctypes.byref(w), ctypes.byref(h))
        return w.value, h.value

    def close(self):
        if hasattr(self, 'loading_texture') and self.loading_texture:
            sdl2.SDL_DestroyTexture(self.loading_texture)
            self.loading_texture = None
        if hasattr(self, 'loading_font') and self.loading_font:
            try:
                import sdl2.sdlttf as sdlttf
                sdlttf.TTF_CloseFont(self.loading_font)
            except: pass
            self.loading_font = None
            
        if self.texture:
            sdl2.SDL_DestroyTexture(self.texture)
            self.texture = None
        if self.renderer:
            sdl2.SDL_DestroyRenderer(self.renderer)
            self.renderer = None
        if self.window:
            sdl2.SDL_HideWindow(self.window)
            sdl2.SDL_DestroyWindow(self.window)
            self.window = None
            
        try:
            import sdl2.sdlttf as sdlttf
            sdlttf.TTF_Quit()
        except: pass
        sdl2.SDL_Quit()
