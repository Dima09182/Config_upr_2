import argparse
import sys
import urllib.request
import tempfile
import tarfile
import os


class DependencyVisualizerCLI:
    def __init__(self):
        self.args = self.parse_arguments()
        self.url = None

    def parse_arguments(self):

        parser = argparse.ArgumentParser(
            description="Dependency Visualizer CLI (Alpine Linux format)"
        )

        parser.add_argument("--package", "-p", required=True,
                            help="Имя анализируемого пакета (например, ansible-2.10.7-r0.apk)")
        parser.add_argument("--repo", "-r", required=True,
                            help="URL или путь к файлу репозитория")
        parser.add_argument("--mode", "-m", choices=["dir", "file", "test", "test2", "auto"],
                            default="auto", help="Режим работы")
        parser.add_argument("--max-depth", "-d", type=int, default=5,
                            help="Максимальная глубина анализа зависимостей")

        args = parser.parse_args()

        if args.max_depth < 0:
            print("Ошибка: глубина не может быть отрицательной")
            sys.exit(1)

        return args

    #извлечение файла из ссылки
    def fetch_package_info(self):
        self.url = f"https://dl-cdn.alpinelinux.org/alpine/v3.14/main/x86_64/{self.args.package}"
        print(f"Попытка получить данные с {self.url}")
        try:
            with urllib.request.urlopen(self.url) as response:
                if response.status == 200:
                    print(f"Ответ сервера: {response.status} ({response.reason})")
                    # сохранения файла во временный файл
                    temp_path = os.path.join(tempfile.gettempdir(), self.args.package)
                    with open(temp_path, "wb") as f:
                        f.write(response.read())
                    print(f"Пакет сохранён во временный файл: {temp_path}")
                    return temp_path
                else:
                    print(f"Ошибка: сервер вернул код {response.status}")
                    return None
        except Exception as e:
            print(f"Ошибка при попытке загрузить {self.url}: {e}")
            return None


    def extract_dependencies(self, apk_path):
        #извлечение зависимостей
        if not apk_path or not os.path.exists(apk_path):
            print("Файл пакета не найден.")
            return

        deps = []
        try:
            with tarfile.open(apk_path, "r:gz") as tar:
                for member in tar.getmembers(): #проход по файлам из apk
                    if member.name == ".PKGINFO":
                        f = tar.extractfile(member) #извлчение данных из файла
                        if f:
                            for line in f:
                                decoded = line.decode("utf-8").strip()
                                if decoded.startswith("depend ="):
                                    deps.append(decoded.replace("depend = ", ""))

            if deps:
                print("\nПрямые зависимости:")
                for dep in deps:
                    print(f" - {dep}")
            else:
                print("Зависимости не найдены")
        except Exception as e:
            print(f"Ошибка при чтении зависимостей: {e}")

    def run(self):
        apk_path = self.fetch_package_info()  # скачивание пакета
        if apk_path:
            self.extract_dependencies(apk_path)  # извлечение зависимостей
        print(f"URL пакета: {self.url}")




if __name__ == "__main__":
    app = DependencyVisualizerCLI()
    app.run()

#python main.py --package acf-gross-0.6.0-r4.apk  --repo repo.txt --mode test --max-depth 3

