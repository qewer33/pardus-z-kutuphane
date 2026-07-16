![banner](./assets/banner.png)

Pardus Z-Kütüphane, Pardus için özel olarak geliştirilmiş, kullanıcı dostu bir **Z-Kitap çalıştırma ve organizasyon aracıdır**. 

Pardus Z-Kütüphane; çalıştırılabilir uygulama (Windows `.exe` veya Linux `.AppImage`), web sitesi ve PDF dosyası formatlarındaki Z-Kitaplarr tek bir arayüz üzerinden yönetmeyi ve çalıştırmayı sağlar. Pardus'un akıllı tahtalarda kullanılan sürümü olan **ETAP** ile birlikte **akıllı tahtalarda, öğretmenler tarafından** ders, konu anlatım ve test kitapları ile kullanılması hedeflenmektedir. Bu hedefe yönelik uygulama, kullanıcı ve akıllı tahta dostu olacak şekilde tasarlanmıştır. Diğer Pardus uygulamaları gibi, Python ve GTK teknolojileri kullanılarak geliştirilmiştir.

Pardus Z-Kütüphane, Gazi Üniversitesi'nden **Anadolu Penguenleri** takımı tarafından, **TEKNOFEST Pardus Hata Yakalama ve Geliştirme Yarışması** için geliştirilmiştir.


![screenshot](./assets/screenshot.png)

## Kullanım

### Kütüphane Görünümü

Uygulamaya eklenen Z-Kitaplar, ızgara şeklindeki kütüphane görünümüne eklenir. Kütüphane görümününde, 

### Kitap Ekleme

Pencerenin sol üst köşesinde bulunan **Ekle** butonu kullanılarak kütüphaneye Z-Kitao eklenebilir. Ekle butonuna tıklandığında **Dosya ekle** ve **Bağlantı ekle** olmak üzere iki seçenek çıkar:

- **Dosya ekleme**: Çalıştırılabilir uygulama (Windows `.exe` veya Linux `.AppImage`/`.fernus`) veya PDF (`.pdf`) dosyaları ***Dosya ekle** seçeneği seçildikten sonra çıkan dosya seçicididen seçilerek eklenebilir. Ayrıca istenilen dosyalar dosya yöneticisi üzerinden Pardus Z-Kütüphane penceresine **sürükle bırak** yapılarak da eklenebilir.
-  **Bağlantı ekleme**: Web kitapları, tarayıcıdan link olarak kopyalanıp **Bağlantı ekle** seçeneği seçildikten sonra açılan penceredeki girdiye yaıştırılarak eklenebilir.

Seçilen yöntem ile ekleme yapıldıktan sonra, **Kitap Ekle** penceresi açılır. Bu pencerede eklenecek kitabın detayları gösterilir. Aynı zamanda kitabın ismini değiştirme, yayıncı seçimi veya etiket ekleme çıkarma da bu pencereden gerçekleştirilebilir. Pardus Z-Kütüphane, dosya ismi ve metadata bilgisinden yayıncı ve etiket çıkarımını otomatik olarak yapma özelliğine sahiptir.

Kitap özellikleri, kitap eklendikten sonra Çalıştır butonunun yanındaki menü içerisindeki **Düzenle** seçeneği seçilerek de düzenlenebilir.

### Kitap Arama ve Filtreleme

Sağ üstte bulunan **arama ikonuna** tıklanınca yukarıdan aılan **arama çubuğu** kullanılarak kütüphanedeki Z-Kitaplar arasında arama yapılabilir.

## Geliştirme ve Altyapı

Proje Meson build sistemini kullanmaktadır. Uygulama, kök dizinindeki `./run.sh` scriptini çalıştırarak çalıştırılabilir.

### Derleme Bağımlılıkları

| Bağımlılık | Açıklama |
|---|---|
| `meson` (>= 1.0.0) | Build sistemi |
| `ninja-build` | Meson tarafından kullanılan derleyici |
| `blueprint-compiler` | `.blp` arayüz dosyalarını derlemek için |
| `libglib2.0-dev-bin` | GSettings şeması derlemek için (`glib-compile-schemas`) |
| `libglib2.0-bin` | GLib çalışma zamanı araçları |
| `desktop-file-utils` | `.desktop` dosyasını doğrulamak için |
| `appstream` | AppStream metainfo dosyasını doğrulamak için |
| `gettext` | Çeviri dosyalarını (`po/`) işlemek için |

### Çalışma Zamanı Bağımlılıkları

| Bağımlılık | Açıklama |
|---|---|
| `python3` | Uygulama çalışma zamanı |
| `python3-gi` | GTK ve Adwaita Python bağlantıları (PyGObject) |
| `gir1.2-gtk-4.0` (>= 4.14) | GTK 4 arayüz kütüphanesi |
| `gir1.2-adw-1` (>= 1.5) | Adwaita stil ve bileşen kütüphanesi |
| `python3-filetype` | Dosya türü tespiti için |
| `wine` | Windows `.exe` dosyalarını çalıştırmak için |
