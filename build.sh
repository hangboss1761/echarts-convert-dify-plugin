#!/bin/bash
# ECharts Convert Plugin 统一构建脚本
# 支持本地开发和 CI/CD
# 合并了根目录和 js-executor 的构建逻辑

set -e

# 配置
MODE="${1:-local}"
INCLUDE_ARM64="${INCLUDE_ARM64:-false}"
CLEAN_BUILD="${CLEAN_BUILD:-false}"

# 颜色输出 (在 CI 中禁用)
if [ "${CI:-false}" = "true" ] || [ "${GITHUB_ACTIONS:-false}" = "true" ]; then
    unset RED GREEN YELLOW BLUE NC
    echo "🚀 构建 ECharts Convert 插件 (CI 模式)..."
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    echo -e "${BLUE}🚀 构建 ECharts Convert 插件 (本地模式)...${NC}"
fi

# 显示帮助
show_help() {
    echo "ECharts Convert Plugin 构建脚本"
    echo ""
    echo "用法: $0 [模式] [选项]"
    echo ""
    echo "模式:"
    echo "  local     本地构建 (默认)"
    echo "  ci        CI/CD 构建"
    echo "  clean     清理构建产物"
    echo "  help      显示此帮助"
    echo ""
    echo "环境变量:"
    echo "  INCLUDE_ARM64=true    包含 ARM64 构建 (默认: false)"
    echo "  CLEAN_BUILD=true      强制重新构建 (默认: false)"
    echo "  CI=true              禁用颜色和额外输出"
    echo ""
    echo "示例:"
    echo "  $0                          # 本地构建 (仅 x64)"
    echo "  $0 ci                       # CI 构建"
    echo "  INCLUDE_ARM64=true $0        # 本地构建包含 ARM64"
    echo "  $0 local 1.0.0              # 指定版本构建"
}

# 检查依赖
check_dependencies() {
    if [ "$MODE" = "local" ]; then
        # 检查 Bun
        if ! command -v bun &> /dev/null; then
            echo -e "${RED}❌ 需要安装 Bun。请先安装 Bun。${NC}"
            exit 1
        fi

        # 检查 gzip
        if ! command -v gzip &> /dev/null; then
            echo -e "${RED}❌ 需要安装 gzip。请先安装 gzip。${NC}"
            exit 1
        fi

        # 检查 dify CLI (可选)
        if ! command -v dify &> /dev/null; then
            echo -e "${YELLOW}⚠️  未找到 dify CLI，将跳过插件包创建${NC}"
        fi
    fi
}

# 读取版本信息
read_version() {
    if [ -n "$1" ]; then
        VERSION="$1"
        echo "🔧 使用指定版本: $VERSION"
        echo "💡 注意: 这将覆盖 manifest.yaml 中的版本"
    else
        if [ -f "manifest.yaml" ]; then
            VERSION=$(grep '^version:' manifest.yaml | awk '{print $2}')
            echo "🔢 从 manifest.yaml 读取版本: $VERSION"
        else
            echo -e "${RED}❌ 未找到 manifest.yaml 文件${NC}"
            exit 1
        fi
    fi
}

# 读取插件元数据
read_plugin_metadata() {
    if [ -f "manifest.yaml" ]; then
        PLUGIN_NAME=$(grep "^name:" manifest.yaml | awk '{print $2}')
        PLUGIN_VERSION=$(grep "^version:" manifest.yaml | awk '{print $2}')
        PLUGIN_AUTHOR=$(grep "^author:" manifest.yaml | awk '{print $2}')

        echo "📋 插件信息:"
        echo "  名称: $PLUGIN_NAME"
        echo "  版本: $PLUGIN_VERSION"
        echo "  作者: $PLUGIN_AUTHOR"

        # 设置包名
        PACKAGE_NAME="${PLUGIN_NAME}-${PLUGIN_VERSION}.difypkg"
    else
        echo -e "${RED}❌ 未找到 manifest.yaml 文件${NC}"
        exit 1
    fi
}

# 清理构建产物
clean_artifacts() {
    echo "🧹 清理构建产物..."
    rm -rf executables/echarts-convert-* *.difypkg *.gz
    echo "✅ 清理完成"
}

# 构建 JavaScript 二进制文件
build_js_binaries() {
    echo "📦 构建 JavaScript 二进制文件..."
    cd js-executor

    # 安装依赖
    echo "  → 安装依赖..."
    bun install

    # 清理旧构建
    echo "  → 清理旧构建..."
    rm -f ../executables/echarts-convert-*

    # 创建输出目录
    mkdir -p ../executables

    # 获取 Bun 版本
    BUN_VERSION=$(bun --version)
    echo "  📦 使用 Bun 版本: $BUN_VERSION"

    # 构建 Linux x64
    echo "  → 构建 Linux x64..."
    bun build ./index.ts ./worker.ts --compile --target=bun-linux-x64 \
        --outfile ../executables/echarts-convert-$VERSION-linux-x64
    if [ $? -eq 0 ]; then
        echo "    ✅ Linux x64 构建成功"
    else
        echo -e "${RED}    ❌ Linux x64 构建失败${NC}"
        exit 1
    fi

    # 构建 Linux ARM64 (可选)
    if [ "$INCLUDE_ARM64" = "true" ]; then
        echo "  → 构建 Linux ARM64..."
        bun build ./index.ts ./worker.ts --compile --target=bun-linux-arm64 \
            --outfile ../executables/echarts-convert-$VERSION-linux-arm64
        if [ $? -eq 0 ]; then
            echo "    ✅ Linux ARM64 构建成功"
        else
            echo -e "${YELLOW}    ⚠️  Linux ARM64 构建失败 (对大多数部署是可选的)${NC}"
        fi
    fi

    # 设置执行权限
    chmod +x ../executables/echarts-convert-* 2>/dev/null

    cd ..
    echo "✅ JavaScript 二进制文件构建完成"
}

# 压缩二进制文件
compress_binaries() {
    echo "🗜️  压缩二进制文件..."
    bin_dir="executables"

    for arch in "x64" "arm64"; do
        binary="$bin_dir/echarts-convert-$VERSION-linux-$arch"
        if [ -f "$binary" ]; then
            echo "  压缩 $arch 二进制文件..."

            # 获取原始大小
            original_size=$(stat -f%z "$binary" 2>/dev/null || stat -c%s "$binary" 2>/dev/null || echo 0)

            # 压缩
            gzip -9 -c "$binary" > "$binary.gz"

            # 获取压缩后大小
            compressed_size=$(stat -f%z "$binary.gz" 2>/dev/null || stat -c%s "$binary.gz" 2>/dev/null || echo 0)

            # 计算压缩率
            if [ "$original_size" -gt 0 ]; then
                reduction=$(echo "scale=1; (1 - $compressed_size / $original_size) * 100" | bc -l 2>/dev/null || echo "N/A")
            else
                reduction="N/A"
            fi

            # 显示压缩结果
            if command -v numfmt &> /dev/null; then
                original_fmt=$(numfmt --to=iec $original_size 2>/dev/null || echo ${original_size}B)
                compressed_fmt=$(numfmt --to=iec $compressed_size 2>/dev/null || echo ${compressed_size}B)
                echo "    $arch: $original_fmt → $compressed_fmt ($reduction% 压缩率)"
            else
                echo "    $arch: 压缩完成"
            fi

            # 删除未压缩文件以节省空间
            rm -f "$binary"

            # 检查压缩后大小是否满足要求
            if [ "$compressed_size" -gt 52428800 ]; then
                echo -e "${YELLOW}    ⚠️  警告: $arch 压缩后文件仍超过 50MB 限制${NC}"
            fi
        else
            echo "  跳过 $arch (文件不存在)"
        fi
    done
    echo "✅ 压缩完成"
}

# 验证构建结果
verify_build() {
    echo "🔍 验证构建结果..."

    local total_size=0
    local files_found=0
    local has_critical_error=false

    for arch in "x64" "arm64"; do
        compressed_file="executables/echarts-convert-$VERSION-linux-$arch.gz"
        if [ -f "$compressed_file" ]; then
            files_found=$((files_found + 1))
            file_size=$(stat -f%z "$compressed_file" 2>/dev/null || stat -c%s "$compressed_file" 2>/dev/null || echo 0)
            total_size=$((total_size + file_size))

            if command -v numfmt &> /dev/null; then
                size_fmt=$(numfmt --to=iec $file_size 2>/dev/null || echo ${file_size}B)
                echo "  ✅ $compressed_file ($size_fmt)"
            else
                echo "  ✅ $compressed_file"
            fi

            # 检查单个文件大小
            if [ "$file_size" -gt 52428800 ]; then
                echo -e "${RED}    ❌ $arch 文件超过 50MB 限制${NC}"
                has_critical_error=true
            fi
        else
            if [ "$arch" = "x64" ]; then
                echo -e "${RED}  ❌ 缺少关键的 $arch 二进制文件${NC}"
                has_critical_error=true
            else
                echo -e "${YELLOW}  ⚠️  缺少 $arch 二进制文件 (可选)${NC}"
            fi
        fi
    done

    echo "📊 总压缩大小: $(numfmt --to=iec $total_size 2>/dev/null || echo ${total_size}B)"

    # 最终验证
    if [ "$has_critical_error" = true ]; then
        echo -e "${RED}❌ 构建验证失败${NC}"
        return 1
    fi

    if [ "$total_size" -gt 52428800 ]; then
        echo -e "${RED}❌ 错误: 总文件大小超过 50MB Dify 限制${NC}"
        return 1
    fi

    if [ "$files_found" -eq 0 ]; then
        echo -e "${RED}❌ 错误: 未找到任何构建文件${NC}"
        return 1
    fi

    echo "✅ 构建验证通过"
    return 0
}


# 打包插件
package_plugin() {
    echo "📦 创建插件包..."

    if [ "$MODE" = "ci" ]; then
        # CI 模式：使用环境变量中的 Dify CLI 路径
        echo "🔍 检查 DIFY_CLI_PATH 环境变量..."
        echo "  DIFY_CLI_PATH: ${DIFY_CLI_PATH:-未设置}"

        if [ -z "$DIFY_CLI_PATH" ]; then
            echo -e "${RED}❌ CI 模式需要设置 DIFY_CLI_PATH 环境变量指向 Dify CLI 工具${NC}"
            exit 1
        fi

        if [ ! -f "$DIFY_CLI_PATH" ]; then
            echo -e "${RED}❌ Dify CLI 工具文件不存在: $DIFY_CLI_PATH${NC}"
            echo "当前工作目录: $(pwd)"
            echo "尝试查找文件..."
            ls -la "$(dirname "$DIFY_CLI_PATH")" 2>/dev/null || echo "目录不存在"
            exit 1
        fi

        echo "✅ Dify CLI 工具已找到: $DIFY_CLI_PATH"

        # 使用官方 CLI 打包
        "$DIFY_CLI_PATH" plugin package . -o "$PACKAGE_NAME"
        if [ $? -eq 0 ]; then
            echo "✅ 包已创建: $PACKAGE_NAME"

            # 验证包文件
            if [ -f "$PACKAGE_NAME" ]; then
                pkg_size=$(stat -f%z "$PACKAGE_NAME" 2>/dev/null || stat -c%s "$PACKAGE_NAME" 2>/dev/null || echo 0)
                size_fmt=$(numfmt --to=iec $pkg_size 2>/dev/null || echo ${pkg_size}B)
                echo "  📊 包大小: $size_fmt"

                if [ "$pkg_size" -gt 52428800 ]; then
                    echo -e "${RED}  ❌ 插件包超过 50MB 限制${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}❌ 包文件未找到${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ 插件包创建失败${NC}"
            exit 1
        fi

    elif [ "$MODE" = "local" ]; then
        # 本地模式：使用本地 dify 命令（可选）
        if command -v dify &> /dev/null; then
            dify plugin package ./ -o echarts-convert.difypkg
            if [ $? -eq 0 ]; then
                echo "✅ 本地包已创建: echarts-convert.difypkg"

                pkg_size=$(stat -f%z "echarts-convert.difypkg" 2>/dev/null || stat -c%s "echarts-convert.difypkg" 2>/dev/null || echo 0)
                if [ "$pkg_size" -gt 52428800 ]; then
                    echo -e "${YELLOW}  ⚠️  警告: 插件包超过 50MB，可能无法上传到 Dify${NC}"
                fi
            else
                echo -e "${RED}❌ 本地插件包创建失败${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}⚠️  dify CLI 未找到，跳过插件包创建${NC}"
            echo "   要创建包，请安装 dify CLI:"
            echo "   https://github.com/langgenius/dify-plugin-daemon"
        fi
    fi
}

# 显示构建总结
show_summary() {
    echo ""
    echo "🎉 构建成功完成！"
    echo "📂 创建的文件:"

    # 显示二进制文件
    for arch in "x64" "arm64"; do
        if [ -f "executables/echarts-convert-$VERSION-linux-$arch.gz" ]; then
            size=$(stat -f%z "executables/echarts-convert-$VERSION-linux-$arch.gz" 2>/dev/null || stat -c%s "executables/echarts-convert-$VERSION-linux-$arch.gz" 2>/dev/null || echo 0)
            size_fmt=$(numfmt --to=iec $size 2>/dev/null || echo ${size}B)
            echo "  - executables/echarts-convert-$VERSION-linux-$arch.gz ($size_fmt)"
        fi
    done

    # 显示插件包
    if [ "$MODE" = "local" ] && [ -f "echarts-convert.difypkg" ]; then
        pkg_size=$(stat -f%z "echarts-convert.difypkg" 2>/dev/null || stat -c%s "echarts-convert.difypkg" 2>/dev/null || echo 0)
        pkg_size_fmt=$(numfmt --to=iec $pkg_size 2>/dev/null || echo ${pkg_size}B)
        echo "  - echarts-convert.difypkg ($pkg_size_fmt)"
        echo ""
        echo "🚀 准备部署！将 echarts-convert.difypkg 上传到 Dify。"
    elif [ "$MODE" = "ci" ] && [ -n "$PACKAGE_NAME" ] && [ -f "$PACKAGE_NAME" ]; then
        pkg_size=$(stat -f%z "$PACKAGE_NAME" 2>/dev/null || stat -c%s "$PACKAGE_NAME" 2>/dev/null || echo 0)
        pkg_size_fmt=$(numfmt --to=iec $pkg_size 2>/dev/null || echo ${pkg_size}B)
        echo "  - $PACKAGE_NAME ($pkg_size_fmt)"
        echo ""
        echo "🚀 CI 包已准备就绪！"
    fi

    # 显示注意事项
    echo ""
    echo "📝 注意事项:"
    echo "  • 仅包含 Linux 二进制文件以最小化插件大小"
    echo "  • 运行时将自动解压二进制文件到缓存目录"
    echo "  • 版本 $VERSION 已嵌入二进制文件名中"
    if [ "$INCLUDE_ARM64" = "true" ]; then
        echo "  • 包含 ARM64 支持 (适用于 ARM 服务器)"
    else
        echo "  • ARM64 支持已禁用，使用 INCLUDE_ARM64=true 启用"
    fi
}

# 主函数
main() {
    # 解析参数和显示帮助
    if [ "$MODE" = "help" ]; then
        show_help
        exit 0
    fi

    if [ "$MODE" = "clean" ]; then
        clean_artifacts
        exit 0
    fi

    # 验证模式
    if [ "$MODE" != "local" ] && [ "$MODE" != "ci" ]; then
        echo -e "${RED}❌ 无效模式: $MODE${NC}"
        echo "使用 'local', 'ci', 'clean', 或 'help'"
        exit 1
    fi

    # 检查依赖
    check_dependencies

    # 检查目录
    if [ ! -f "manifest.yaml" ] || [ ! -d "js-executor" ]; then
        echo -e "${RED}❌ 请在插件根目录运行${NC}"
        exit 1
    fi

    # 读取版本
    read_version "$2"

    # 如果是强制清理，先清理
    if [ "$CLEAN_BUILD" = "true" ]; then
        echo "🧹 强制清理构建产物..."
        rm -rf executables/echarts-convert-*
    fi

    # 执行构建步骤
    build_js_binaries
    compress_binaries

    # CI 模式额外步骤
    if [ "$MODE" = "ci" ]; then
        read_plugin_metadata
    fi

    # 验证构建结果
    if verify_build; then
        package_plugin
        show_summary
        echo -e "${GREEN}✅ 所有步骤完成！${NC}"
    else
        echo -e "${RED}❌ 构建失败，请检查错误信息${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"