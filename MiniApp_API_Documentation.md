# 微信小程序 - AI解题/批改API接口文档

## 📋 接口概述

**接口名称**：图片智能解析接口（解题/批改）

**接口描述**：接收一张Base64编码的题目图片，根据指定模式返回AI的详细解答或批改结果。支持数学、物理、化学等多学科题目的智能处理。

---

## 🔗 接口信息

### 请求URL
```
POST http://127.0.0.1:8000/process_image_for_miniapp
```

### 请求方法
```
POST
```

### 请求头 (Header)
```json
{
  "Content-Type": "application/json"
}
```

---

## 📤 请求参数

### 请求体 (Request Body)

**格式**：JSON

**参数说明**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `image_base_64` | string | ✅ 是 | 用户上传的题目图片，经过Base64编码的字符串 |
| `mode` | string | ✅ 是 | 操作模式，可选值：<br/>• `"solve"` - 解题模式<br/>• `"review"` - 批改模式 |

### 请求示例

**解题模式**：
```json
{
  "image_base_64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "mode": "solve"
}
```

**批改模式**：
```json
{
  "image_base_64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "mode": "review"
}
```

---

## 📥 响应结果

### 成功响应

**HTTP状态码**：`200 OK`

**响应体格式**：

```json
{
  "status": "success",
  "result": "AI生成的详细解答或批改内容（Markdown格式）"
}
```

### 成功响应示例

**解题模式响应**：
```json
{
  "status": "success",
  "result": "## 题目解答\n\n### 第1题\n\n**题目分析**：这是一道关于二项式定理的题目...\n\n**解题步骤**：\n\n1. 首先，我们根据二项式定理展开 $(1+x)^{2n+1}$：\n   $$\n   (1+x)^{2n+1} = \\sum_{k=0}^{2n+1} \\binom{2n+1}{k} x^k\n   $$\n\n2. 对比系数可得：\n   - $a_0 = \\binom{2n+1}{0} = 1$\n   - $a_k = \\binom{2n+1}{k}$\n\n3. 因此...\n\n**答案**：$\\binom{2n+1}{n} = \\binom{2n}{n} + \\binom{2n}{n-1}$"
}
```

**批改模式响应**：
```json
{
  "status": "success",
  "result": "## 批改结果\n\n### 第1题批改\n\n**学生答案**：$(1+x)^{2n+1} = ...$\n\n**批改意见**：\n- ✅ 展开式正确\n- ❌ 第3步计算有误，应该是 $\\binom{2n+1}{n}$ 而非 $\\binom{2n}{n}$\n\n**正确解法**：\n根据组合数的性质...\n\n**最终评价**：本题答案部分正确，需要注意组合数的计算。"
}
```

---

### 失败响应

**HTTP状态码**：`500 Internal Server Error`

**响应体格式**：

```json
{
  "status": "error",
  "message": "具体的错误信息"
}
```

### 失败响应示例

```json
{
  "status": "error",
  "message": "ValueError: Invalid base64-encoded string"
}
```

**常见错误原因**：
- Base64编码格式错误
- 图片格式不支持
- AI服务暂时不可用
- 网络连接超时

---

## 💡 特别说明

### 1. 返回结果格式

返回的 `result` 字段内容为 **Markdown格式**，包含以下特点：

- ✅ **支持富文本**：包含标题、列表、粗体等Markdown语法
- ✅ **LaTeX公式**：数学公式已按标准格式嵌入
  - 行内公式：`$...$`，例如 `$x^2 + y^2 = r^2$`
  - 块级公式：`$$...$$`，例如：
    ```
    $$
    \int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
    $$
    ```

### 2. 前端渲染建议

**小程序端需要**：
1. 使用Markdown解析库（如 `towxml`, `wxParse`）渲染文本
2. 使用MathJax或KaTeX渲染LaTeX公式
3. 建议先解析Markdown，再对LaTeX部分进行公式渲染

**示例流程**：
```
AI返回的Markdown文本
    ↓
Markdown解析（保留LaTeX标记）
    ↓
LaTeX公式渲染（$...$和$$...$$）
    ↓
最终显示
```

### 3. 图片编码要求

- **格式**：支持 PNG, JPEG, JPG
- **编码**：标准Base64编码
- **大小**：建议 < 10MB（编码前）
- **清晰度**：建议至少 720p，以确保OCR识别准确

**微信小程序Base64编码示例**：
```javascript
// 选择图片
wx.chooseImage({
  count: 1,
  success: function(res) {
    const tempFilePath = res.tempFilePaths[0];
    
    // 读取文件为Base64
    wx.getFileSystemManager().readFile({
      filePath: tempFilePath,
      encoding: 'base64',
      success: function(data) {
        const base64String = data.data;
        
        // 调用API
        wx.request({
          url: 'http://your-server:8000/process_image_for_miniapp',
          method: 'POST',
          data: {
            image_base_64: base64String,
            mode: 'solve'  // 或 'review'
          },
          success: function(response) {
            if (response.data.status === 'success') {
              console.log('AI解答:', response.data.result);
              // 渲染Markdown内容
            } else {
              console.error('错误:', response.data.message);
            }
          }
        });
      }
    });
  }
});
```

### 4. 性能说明

- **预计响应时间**：
  - OCR识别：2-5秒
  - AI生成：10-30秒
  - 总计：15-35秒
  
- **建议**：
  - 在小程序端显示加载动画
  - 设置请求超时时间为 60秒
  - 考虑实现重试机制

### 5. 模式说明

**`solve` - 解题模式**：
- 适用场景：学生遇到难题，需要详细解答
- AI行为：提供完整的解题步骤、思路分析、知识点讲解
- 返回内容：题目分析、解题步骤、最终答案

**`review` - 批改模式**：
- 适用场景：学生完成作业后，需要检查对错
- AI行为：批改学生答案，指出错误，给出正确解法
- 返回内容：批改意见、错误指正、正确答案

---

## 🔒 注意事项

### 安全性

1. **API Key管理**：
   - 后端服务依赖阿里云通义千问API
   - 请勿在小程序端暴露API Key
   - 建议通过后端服务转发请求

2. **数据隐私**：
   - 图片数据仅用于临时处理
   - 不会永久存储用户上传的图片
   - AI处理的数据符合隐私保护要求

### 错误处理

建议在小程序端实现以下错误处理：

```javascript
wx.request({
  url: 'http://your-server:8000/process_image_for_miniapp',
  method: 'POST',
  data: requestData,
  timeout: 60000,  // 60秒超时
  success: function(res) {
    if (res.data.status === 'success') {
      // 处理成功结果
      renderMarkdown(res.data.result);
    } else {
      // 处理业务错误
      wx.showToast({
        title: '处理失败：' + res.data.message,
        icon: 'none'
      });
    }
  },
  fail: function(err) {
    // 处理网络错误
    wx.showToast({
      title: '网络错误，请重试',
      icon: 'none'
    });
  }
});
```

---

## 📞 技术支持

如有问题，请联系后端技术团队或参考：
- 后端API文档：`http://127.0.0.1:8000/docs`
- 项目技术文档：`沐梧AI解题系统_技术文档.md`

---

**版本**：V1.0  
**更新时间**：2025-10-20  
**兼容性**：后端 V24.6+

