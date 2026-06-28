local SERVER_URL = "https://unawake-impart-trio.ngrok-free.dev"
local POLL_INTERVAL = 10
local NameStore = game:GetService("ServerStorage"):WaitForChild("NameStore")

local function fetchFromServer()
	local success, result = pcall(function()
		local http = game:GetService("HttpService")
		local response = http:GetAsync(SERVER_URL .. "/poll", false)
		return http:JSONDecode(response)
	end)

	if success and result then
		return result
	else
		warn("Failed to fetch from server: " .. tostring(result))
		return nil
	end
end

local function updateNameStore(data)
	if not data then return end

	local settings = NameStore:WaitForChild("Settings") or NameStore
	if typeof(settings) == "function" then
		settings = settings()
	end

	if data.CustomNames then
		for userId, name in pairs(data.CustomNames) do
			settings.CustomNames[userId] = name
		end
	end

	if data.UserTags then
		for userId, tagData in pairs(data.UserTags) do
			settings.UserTags[userId] = {
				Tag = tagData.tag,
				Color = Color3.fromRGB(tagData.r, tagData.g, tagData.b)
			}
		end
	end

	if data.GroupTags then
		for groupId, tagData in pairs(data.GroupTags) do
			settings.GroupTags[groupId] = {
				Tag = tagData.tag,
				Color = Color3.fromRGB(tagData.r, tagData.g, tagData.b)
			}
		end
	end

	if data.RankTagColors then
		for userId, colorData in pairs(data.RankTagColors) do
			settings.RankTagColors[userId] = Color3.fromRGB(colorData.r, colorData.g, colorData.b)
		end
	end

	if data.CustomRankUsername then
		for userId, username in pairs(data.CustomRankUsername) do
			settings.CustomRankUsername[userId] = username
		end
	end
end

print("NameStoreUpdater started — polling every " .. POLL_INTERVAL .. " seconds")

while true do
	wait(POLL_INTERVAL)
	local data = fetchFromServer()
	if data then
		updateNameStore(data)
		print("NameStore updated from server")
	end
end
