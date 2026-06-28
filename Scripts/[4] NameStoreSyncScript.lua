local SERVER_URL = "https://unawake-impart-trio.ngrok-free.dev"
local SYNC_INTERVAL = 3
local NameStore = game:GetService("ServerStorage"):WaitForChild("NameStore")
local lastSyncData = ""

local function getNameStoreData()
	local settings = NameStore:WaitForChild("Settings") or NameStore
	if typeof(settings) == "function" then
		settings = settings()
	end

	return {
		CustomNames = settings.CustomNames or {},
		UserTags = settings.UserTags or {},
		GroupTags = settings.GroupTags or {},
		RankTagColors = settings.RankTagColors or {},
		CustomRankUsername = settings.CustomRankUsername or {}
	}
end

local function convertToJSON(data)
	local http = game:GetService("HttpService")
	return http:JSONEncode(data)
end

local function syncToServer(data)
	local success, result = pcall(function()
		local http = game:GetService("HttpService")
		local response = http:PostAsync(
			SERVER_URL .. "/push",
			http:JSONEncode({
				type = "Sync",
				data = data
			}),
			Enum.HttpContentType.ApplicationJson,
			false,
			{
				["x-secret"] = "changeme123"
			}
		)
		return http:JSONDecode(response)
	end)

	if success then
		print("Synced NameStore to server")
		return true
	else
		warn("Failed to sync NameStore: " .. tostring(result))
		return false
	end
end

print("NameStoreSyncScript started — syncing every " .. SYNC_INTERVAL .. " seconds")

while true do
	wait(SYNC_INTERVAL)

	local currentData = convertToJSON(getNameStoreData())

	if currentData ~= lastSyncData then
		syncToServer(getNameStoreData())
		lastSyncData = currentData
	end
end
