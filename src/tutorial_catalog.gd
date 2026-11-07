extends RefCounted
# Existing course identities/checkpoints remain owned by LessonStore. This index
# only organizes entry points; choosing a topic starts its validated first task.
const SECTIONS=[
	{"level":"Basic","title":"Start here","courses":[{"id":"first-movie-v1","description":"Make a first film: import, select, pose, draw, edit timing and render. Save your practice when you want to keep it."}]},
	{"level":"Basic","title":"Drawing and posing","courses":[{"id":"basic-pose","description":"Select the practice figure, key an arm pose and draw on Ink."}]},
	{"level":"Advanced","title":"Camera and rendering","courses":[{"id":"advanced-camera","description":"Record camera shots and field of view."},{"id":"advanced-lighting-v1","description":"Compare scene lighting and render a finished movie."}]},
	{"level":"Advanced","title":"Animation and posing","courses":[{"id":"advanced-interpolation-v1","description":"Shape motion timing with interpolation and editable curves."},{"id":"advanced-constraints-v1","description":"Pose the rig, plant the feet and edit constrained root movement."}]},
	{"level":"Advanced","title":"Physics","courses":[{"id":"advanced-physics-v1","description":"Run and freeze simulation, record a Local take, preview and render it."}]}
]
