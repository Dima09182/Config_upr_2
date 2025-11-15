import argparse
import sys
import urllib.request
import tempfile
import tarfile
import os
from collections import deque


class DependencyVisualizerCLI:
    def __init__(self):
        self.args = self.parse_arguments()
        self.url = None
        index_path = self.download_index()
        self.index = self.parse_index(index_path)
    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Dependency Visualizer CLI"
        )

        parser.add_argument("--package", "-p", required=True,
                            help="Имя анализируемого пакета (например, ansible-2.10.7-r0.apk)")

        parser.add_argument("--repo", "-r", required=True,
                            help="URL или путь к файлу репозитория")

        parser.add_argument("--mode", "-m",
                            choices=["auto", "file", "dir", "test", "test2"],
                            default="auto",
                            help="Режим работы")

        parser.add_argument("--max-depth", "-d", type=int, default=5,
                            help="Максимальная глубина для BFS")

        args = parser.parse_args()

        if args.max_depth < 0:
            print("Ошибка: глубина не может быть отрицательной")
            sys.exit(1)

        return args


    #  загрузка апк по имени

    def fetch_package_info(self, pkg_name=None):
        #Скачивает APK по короткому или полному имени
        if pkg_name is None:
            pkg_name = self.args.package

        # Если передали короткое имя → ищем полное
        if not pkg_name.endswith(".apk"):
            if pkg_name in self.index:
                pkg_name = self.index[pkg_name]
            else:
                print(f"Не найдено в индексе: {pkg_name}")
                return None

        self.url = f"https://dl-cdn.alpinelinux.org/alpine/v3.14/main/x86_64/{pkg_name}"
        print(f"Скачивание: {self.url}")

        try:
            temp_path = os.path.join(tempfile.gettempdir(), pkg_name)
            urllib.request.urlretrieve(self.url, temp_path)
            print(f"Файл сохранён: {temp_path}")
            return temp_path

        except Exception as e:
            print(f"Не удалось скачать пакет: {pkg_name} — {e}")
            return None

    #  извлечение зависимостей


    def get_dependencies(self, apk_path):
        if not apk_path or not os.path.exists(apk_path):
            return []

        deps = []

        try:
            with tarfile.open(apk_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name == ".PKGINFO":
                        f = tar.extractfile(member)
                        for line in f:
                            decoded = line.decode().strip()
                            if decoded.startswith("depend ="):
                                deps.append(decoded.replace("depend = ", ""))
        except:
            print(f"Ошибка чтения {apk_path}")

        return deps


    def load_test_repo(self):
        repo_graph = {}

        try:
            with open(self.args.repo, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    if ":" not in line:
                        continue

                    pkg, deps = line.split(":", 1)
                    pkg = pkg.strip()
                    deps = deps.strip()

                    if deps == "":
                        repo_graph[pkg] = []
                    else:
                        repo_graph[pkg] = deps.split()

            print("\nТестовый репозиторий загружен:")
            for k, v in repo_graph.items():
                print(f"{k} → {v}")

        except Exception as e:
            print("Ошибка чтения тестового репозитория:", e)
            sys.exit(1)

        return repo_graph

    def download_index(self):
        #Скачивает APKINDEX.tar.gz из репозитория Alpine
        index_url = "https://dl-cdn.alpinelinux.org/alpine/v3.14/main/x86_64/APKINDEX.tar.gz"
        temp_path = os.path.join(tempfile.gettempdir(), "APKINDEX.tar.gz")

        try:
            urllib.request.urlretrieve(index_url, temp_path)
            print(f"Индекс репозитория скачан: {temp_path}")
            return temp_path
        except Exception as e:
            print(f"Ошибка скачивания APKINDEX: {e}")
            return None

    def parse_index(self, index_path):
        #создаёт словарь: имя → имя-версия-релиз.apk
        if not index_path or not os.path.exists(index_path):
            return {}

        mapping = {}  # {"acf-core": "acf-core-0.7.4-r0.apk"}

        try:
            import tarfile
            with tarfile.open(index_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith("APKINDEX"):
                        f = tar.extractfile(member)
                        if not f:
                            continue

                        pkg_name = None
                        pkg_ver = None

                        for line in f.read().decode().splitlines():
                            if line.startswith("P:"):
                                pkg_name = line[2:]
                            elif line.startswith("V:"):
                                pkg_ver = line[2:]

                                if pkg_name and pkg_ver:
                                    mapping[pkg_name] = f"{pkg_name}-{pkg_ver}.apk"
                                    pkg_name = None
                                    pkg_ver = None

            print(f"В индексе найдено пакетов: {len(mapping)}")
            return mapping

        except Exception as e:
            print(f"Ошибка парсинга APKINDEX: {e}")
            return {}


    # BFS

    def build_graph_bfs(self):
        print("\nПостроение графа (BFS)")

        queue = deque([(self.args.package, 0)])
        visited = set()
        graph = {}

        while queue:
            pkg, depth = queue.popleft()

            if depth > self.args.max_depth:
                continue

            if pkg in visited:
                continue

            visited.add(pkg)

            # в режиме тест все зависимости из файла
            if self.args.mode == "test":
                deps = self.test_repo_graph.get(pkg, [])
                graph[pkg] = {"deps": deps, "depth": depth}
            else:
                # обычный режим - из apk
                apk_path = self.fetch_package_info(pkg)
                deps = self.get_dependencies(apk_path)
                graph[pkg] = {"deps": deps, "depth": depth}

            for dep in deps:
                queue.append((dep, depth + 1))

        return graph



    def run(self):

        if self.args.mode == "test":
            self.test_repo_graph = self.load_test_repo()

        graph = self.build_graph_bfs()
        if self.args.mode != "test":
            print("\nИтоговый граф зависимостей")
            for pkg, info in graph.items():
                indent = " " * 4 * info["depth"]
                print(f"{indent}{pkg}: {info['deps']}")


if __name__ == "__main__":
    app = DependencyVisualizerCLI()
    app.run()




#python main.py --package acf-pingu-0.4.0-r4.apk --repo repo.txt --mode auto --max-depth 3

#python main.py --package acf-pingu-0.4.0-r4.apk --repo repo.txt --mode test --max-depth 3