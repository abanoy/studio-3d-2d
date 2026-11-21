extends ConfirmationDialog
## Source-site handoff only. Never retrieves content or launches a game.
signal source_confirmed(url: String, provider: String, remember: bool)
var remember: CheckBox
var explanation: Label
var _url := ""
var _provider := ""

static func provider_for_url(url: String) -> String:
	if not url.begins_with("https://steamcommunity.com/"): return ""
	var query := url.get_slice("?", 1)
	for parameter in query.split("&"):
		if parameter == "appid=1840": return "steam_sfm"
		if parameter == "appid=4000": return "steam_gmod"
	return ""

func _ready() -> void:
	title = "Before opening Steam Workshop"
	ok_button_text = "Open source website"; cancel_button_text = "Cancel"
	var column := VBoxContainer.new(); add_child(column)
	explanation = Label.new(); explanation.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	explanation.custom_minimum_size.x = 520; column.add_child(explanation)
	remember = CheckBox.new(); remember.text = "Do not show again for this source"; column.add_child(remember)
	confirmed.connect(_confirm)
	canceled.connect(dismiss)
	close_requested.connect(dismiss)

func present(url: String, provider: String, local_context: String) -> void:
	_url = url; _provider = provider
	remember.button_pressed = false
	var application := "Source Filmmaker" if provider == "steam_sfm" else "Garry's Mod"
	explanation.text = "This opens the %s Workshop website. Studio does not download, subscribe to, install or convert Workshop items.\n\nSteam sign-in, the source application or content from other games may be needed for an individual item. Check its source page and listed requirements. Access and retrieval remain with the source website and Steam.\n\n%s\n\nA detected folder is not proof of ownership, a license or permission to use an item." % [application, local_context]
	popup_centered(Vector2i(580, 360))

func dismiss() -> void:
	_url = ""; _provider = ""; hide()

func _confirm() -> void:
	var url := _url; var provider := _provider; var save := remember.button_pressed
	dismiss()
	if not url.is_empty(): source_confirmed.emit(url, provider, save)
