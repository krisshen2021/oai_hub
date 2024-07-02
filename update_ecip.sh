#!/bin/bash

# 日志文件路径
LOG_FILE="/var/log/route53-update.log"

# 函数：记录日志
log() {
    echo "$(date): $1" >> $LOG_FILE
}

# 函数：错误处理
handle_error() {
    log "错误: $1"
    exit 1
}

# 检查是否有 root 权限
if [ "$(id -u)" != "0" ]; then
   handle_error "此脚本需要 root 权限运行"
fi

# 安装 AWS CLI
install_aws_cli() {
    log "开始安装 AWS CLI..."
    apt update
    apt install -y unzip curl
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
    log "AWS CLI 安装完成"
}

# 检查 AWS CLI 是否安装，如果没有则安装
if ! command -v aws &> /dev/null; then
    log "AWS CLI 未安装，正在安装..."
    install_aws_cli
else
    log "AWS CLI 已安装"
fi

# 验证 AWS CLI 配置
aws sts get-caller-identity >/dev/null 2>&1 || handle_error "AWS CLI 未正确配置或没有足够的权限"

# 设置你的域名和托管区域ID
HOSTED_ZONE_ID="Z10271193II7TLH9NEAHK"
DOMAIN_NAME="muffinchatbar.com"
WWW_DOMAIN_NAME="www.muffinchatbar.com"

# 获取实例的公共IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# 检查是否成功获取IP
if [ -z "$PUBLIC_IP" ]; then
    handle_error "无法获取公共 IP"
fi

log "获取到的公共 IP: $PUBLIC_IP"

# 创建 Route 53 更新批处理文件
TEMP_FILE=$(mktemp)
cat > $TEMP_FILE << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "${DOMAIN_NAME}",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{ "Value": "${PUBLIC_IP}" }]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "${WWW_DOMAIN_NAME}",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{ "Value": "${PUBLIC_IP}" }]
      }
    }
  ]
}
EOF

# 使用 AWS CLI 更新 Route 53 记录
log "正在更新 Route 53 记录..."
UPDATE_RESULT=$(aws route53 change-resource-record-sets \
  --hosted-zone-id ${HOSTED_ZONE_ID} \
  --change-batch file://$TEMP_FILE 2>&1)

if [ $? -eq 0 ]; then
    log "成功更新 Route 53 记录"
    log "更新结果: $UPDATE_RESULT"
else
    handle_error "更新 Route 53 记录失败: $UPDATE_RESULT"
fi

# 清理临时文件