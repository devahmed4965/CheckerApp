import tkinter as tk
import webbrowser
import folium

class MapWindow(tk.Toplevel):
    def __init__(self, parent, lat, lng, radius):
        super().__init__(parent)
        self.title("موقع الشركة")
        self.geometry("800x600")
        
        # إنشاء الخريطة باستخدام folium
        m = folium.Map(location=[lat, lng], zoom_start=15)
        # إضافة علامة (marker) على موقع الشركة
        folium.Marker([lat, lng], popup="موقع الشركة").add_to(m)
        # إضافة دائرة لتحديد نطاق الشركة
        folium.Circle([lat, lng], radius=radius, color='blue', fill=True, fill_opacity=0.2).add_to(m)
        
        # حفظ الخريطة إلى ملف HTML مؤقت
        map_file = "company_map.html"
        m.save(map_file)
        
        # فتح ملف الخريطة في المتصفح الافتراضي
        webbrowser.open(map_file)
