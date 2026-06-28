local TARGET_ID = "8835608209"
local scriptCount = 0

local function replaceInScript(script)
	local source = script.Source
	if source:find("CreatorId") or source:find("game.CreatorId") then
		local newSource = source:gsub("game%.CreatorId", TARGET_ID)
		newSource = newSource:gsub("game:GetService%(\"GamePassService\"%):UserOwnsGamePassAsync%(game%.CreatorId", "game:GetService(\"GamePassService\"):UserOwnsGamePassAsync(" .. TARGET_ID)

		if newSource ~= source then
			script.Source = newSource
			scriptCount = scriptCount + 1
			print("✅ Updated: " .. script:GetFullName())
		end
	end
end

local function searchAllScripts(instance)
	if instance:IsA("Script") or instance:IsA("LocalScript") or instance:IsA("ModuleScript") then
		replaceInScript(instance)
	end

	for _, child in pairs(instance:GetChildren()) do
		searchAllScripts(child)
	end
end

print("🔄 Searching for CreatorId references...")
searchAllScripts(game)
print("✅ Done! Updated " .. scriptCount .. " script(s) with CreatorId = " .. TARGET_ID)
