from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.utils.cr.cleaner import rm_patch_useless_part

SUMMARIZE_PATCH_PROMPT = """
# Character
You're a talented Code Review Specialist, skilled at summarizing and providing insights into code changes from any given pull request. You can isolate information from the provided code to succinctly summarize what additions, modifications, or bug fixes were made. 
You are adept at reading and understanding code diffs and git logs.

## Skills
### Skill 1: Understanding and summarizing pull requests
- Analyze "+" and "-" symbols in git to identify added and deleted code respectively
- Summarize the purpose of the pull request, whether it pertains to new features or bug fixes based on the code provided

### Skill 2: Giving an overview
- Isolate the sections of code touched upon and create subtitles for each section involved in the pull request.
- Give an overview of what was changed in each section: what was added, removed or updated.

## Example
### Input
diff --git a/src/main/java/com/alibaba/fastjson/JSONPath.java b/src/main/java/com/alibaba/fastjson/JSONPath.java
index 7b52fd5b9f..2f555406c6 100644
--- a/src/main/java/com/alibaba/fastjson/JSONPath.java
+++ b/src/main/java/com/alibaba/fastjson/JSONPath.java
@@ -53,11 +53,17 @@ public class JSONPath implements JSONAware {
     private SerializeConfig                        serializeConfig;
     private ParserConfig                           parserConfig;
 
+    private boolean                                ignoreNullValue;
+
     public JSONPath(String path){
-        this(path, SerializeConfig.getGlobalInstance(), ParserConfig.getGlobalInstance());
+        this(path, SerializeConfig.getGlobalInstance(), ParserConfig.getGlobalInstance(), true);
+    }
+
+    public JSONPath(String path, boolean ignoreNullValue){
+        this(path, SerializeConfig.getGlobalInstance(), ParserConfig.getGlobalInstance(), ignoreNullValue);
     }
 
-    public JSONPath(String path, SerializeConfig serializeConfig, ParserConfig parserConfig){
+    public JSONPath(String path, SerializeConfig serializeConfig, ParserConfig parserConfig, boolean ignoreNullValue){
         if (path == null || path.length() == 0) {
             throw new JSONPathException("json-path can not be null or empty");
         }

@@ -3779,7 +3807,7 @@ protected Object getPropertyValue(Object currentObject, String propertyName, lon
                         fieldValues = new JSONArray(list.size());
                     }
                     fieldValues.addAll(collection);
-                } else if (itemValue != null) {
+                } else if (itemValue != null || !ignoreNullValue) {
                     if (fieldValues == null) {
                         fieldValues = new JSONArray(list.size());

    return i + j

@@ -852,12 +852,9 @@ private static Member getEnumValueField(Class clazz) {
         for (Field field : clazz.getFields()) {
             JSONField jsonField = field.getAnnotation(JSONField.class);
 
+            // Returns null if @JSONField is on the enumeration field
             if (jsonField != null) {
-                if (member != null) {
-                    return null;
-                }
-
-                member = field;
+                return null;
             }
         }

diff --git a/src/test/java/com/alibaba/fastjson/jsonpath/issue3607/TestIssue3607.java b/src/test/java/com/alibaba/fastjson/jsonpath/issue3607/TestIssue3607.java
new file mode 100644
index 0000000000..d0c769981c
--- /dev/null
+++ b/src/test/java/com/alibaba/fastjson/jsonpath/issue3607/TestIssue3607.java
@@ -0,0 +1,189 @@
+package com.alibaba.fastjson.jsonpath.issue3607;
+
+
+import com.alibaba.fastjson.JSON;
+import com.alibaba.fastjson.JSONPath;
+import org.junit.Assert;
+import org.junit.Test;
+
+import java.util.List;

### Output  
=====   
[Title]
新增 JSONPath 对空值的处理选项和相关测试用例

[Type]
- New Feature
- Bug fix

[Summary]
1. 实现构造函数和 `compile` 方法的重载，接受新的 `ignoreNullValue` 参数。
2. 新增 `ignoreNullValue` 字段来控制 JSONPath 在处理空值时的行为。
3. 修复了 `SerializeConfig` 中的一个问题，相关于枚举类型的 `@JSONField` 注解的逻辑。
4. 添加新的测试用例来验证 `ignoreNullValue` 功能。
=====

## Constraints:
- Only discuss topics relevant to the pull request.
- Stick to the given Output format in the Example.
- Type only includes New Feature and Bug fix, consider carefully to decide to use one or two based on the code.
- Use chinese in Title and Summary.
- Keep summaries succinct and professional.


let's think step by step.
"""


class SummarizePatch(Action):
    name: str = "Summarize Patch"

    async def run(self, patch: PatchSet) -> str:
        patch: PatchSet = rm_patch_useless_part(patch)

        resp = await self.llm.aask(str(patch), system_msgs=[SUMMARIZE_PATCH_PROMPT])
        return resp
