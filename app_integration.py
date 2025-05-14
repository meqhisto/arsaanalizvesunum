# Bu dosyayı çalıştırarak yeni task route'larını ana uygulamaya entegre edin
from app import app
from crm_task_routes import init_app

if __name__ == "__main__":
    # Task Blueprint'i kaydet
    init_app(app)
    print("Görev takip sistemi başarıyla entegre edildi!")
    print("Şimdi uygulamayı yeniden başlatın.")
