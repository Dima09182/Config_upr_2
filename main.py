import argparse
import sys

class Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Error in arguments: {message}")
        #self.print_help() #вывод подсказок
        sys.exit(1)

def main():
    parser = Parser(description="Minimal CLI for the dependency Visualizer")

    parser.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", "-r", required=True, help="URL или путь к файлу репозитория")
    parser.add_argument("--mode", "-m", choices=["dir", "file", "test", "test2", "auto"], default="auto",
                        help="Режим работы")
    parser.add_argument("--max-depth", "-d", type=int, default=5, help="Максимальная глубина")#по умолчанию 5

    args = parser.parse_args()

    # Проверка на отрицательную глубину
    if args.max_depth < 0:
        print("Ошибка: глубина не может быть отрицательной")
        sys.exit(1)

    print(f"package={args.package}")
    print(f"repo={args.repo}")
    print(f"mode={args.mode}")
    print(f"max-depth={args.max_depth}")

if __name__ == "__main__":
    main()
#python main.py --package testpkg --repo repo.txt --mode test --max-depth 3
