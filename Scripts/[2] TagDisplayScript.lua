local SERVER_URL = "https://unawake-impart-trio.ngrok-free.dev"
local POLL_INTERVAL = 5
local NameStore = game:GetService("ServerStorage"):WaitForChild("NameStore")

local function createTagGui(player, character)
	local humanoidRootPart = character:FindFirstChild("HumanoidRootPart")
	if not humanoidRootPart then return end

	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.new(4, 0, 2, 0)
	billboard.StudsOffset = Vector3.new(0, 3, 0)
	billboard.MaxDistance = 100
	billboard.Parent = humanoidRootPart

	local textLabel = Instance.new("TextLabel")
	textLabel.BackgroundTransparency = 1
	textLabel.TextScaled = true
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextColor3 = Color3.new(1, 1, 1)
	textLabel.Size = UDim2.new(1, 0, 1, 0)
	textLabel.Parent = billboard

	return textLabel
end

local function updatePlayerTag(player, character)
	local userId = tostring(player.UserId)
	local settings = NameStore:WaitForChild("Settings") or NameStore
	if typeof(settings) == "function" then settings = settings() end

	local textLabel = character:FindFirstChild("HumanoidRootPart"):FindFirstChild("BillboardGui"):FindFirstChild("TextLabel") or createTagGui(player, character)

	local displayText = ""

	if settings.CustomNames and settings.CustomNames[userId] then
		displayText = settings.CustomNames[userId]
	else
		displayText = player.Name
	end

	if settings.UserTags and settings.UserTags[userId] then
		local userTag = settings.UserTags[userId]
		displayText = "[" .. userTag.Tag .. "] " .. displayText
		textLabel.TextColor3 = userTag.Color
	elseif settings.GroupTags then
		for groupId, tagData in pairs(settings.GroupTags) do
			if pcall(function()
				return game:GetService("GroupService"):GetGroupInfoAsync(tonumber(groupId))
			end) then
				textLabel.TextColor3 = tagData.Color
				displayText = "[" .. tagData.Tag .. "] " .. displayText
				break
			end
		end
	end

	textLabel.Text = displayText
end

game.Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		wait(0.5)
		local humanoidRootPart = character:FindFirstChild("HumanoidRootPart")
		if humanoidRootPart and not humanoidRootPart:FindFirstChild("BillboardGui") then
			createTagGui(player, character)
		end
		updatePlayerTag(player, character)
	end)
end)

while true do
	wait(POLL_INTERVAL)
	for _, player in pairs(game.Players:GetPlayers()) do
		if player.Character then
			pcall(function()
				updatePlayerTag(player, player.Character)
			end)
		end
	end
end
