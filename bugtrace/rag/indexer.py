# bugtrace/rag/indexer.py
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import hashlib
import json

from bugtrace.utils.fs import ensure_state_dir, load_manifest
from bugtrace.utils.state import StateManager
from bugtrace.config.settings import load_user_config, validate_config

console = Console()


def hash_config(config: dict) -> str:
    """Generate hash of config for change detection."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()


def index_project(project_root: Path, force: bool = False):
    """
    Main indexing function with full state management.
    
    Args:
        project_root: Root directory of the project
        force: If True, forces full re-index regardless of state
    """
    console.print("[bold]Building RAG Index[/bold]\n")
    
    state_dir = ensure_state_dir(project_root)
    state_manager = StateManager(state_dir)
    
    # Step 1: Check if manifest exists
    console.print("[dim]1. Checking project scan status...[/dim]")
    manifest_path = state_dir / "manifest.json"
    

    from bugtrace.analyze.core import analyze as scan_project
    scan_project(project_root)
    console.print("   [green]✓ Scan complete[/green]\n")
    
    # Step 2: Load and validate config
    console.print("[dim]2. Loading configuration...[/dim]")
    config = load_user_config(project_root)
    
    try:
        validate_config(config)
        console.print("   [green]✓ Configuration valid[/green]")
    except ValueError as e:
        console.print(f"   [red]✗ Invalid configuration:[/red]\n{e}")
        raise
    
    # Step 3: Check for config changes
    console.print("[dim]3. Checking for configuration changes...[/dim]")
    current_config_hash = hash_config(config)
    config_changed = state_manager.config_changed(current_config_hash)
    
    if config_changed:
        console.print("   [yellow]⚠ Configuration changed - full re-index required[/yellow]")
        force = True  # Config change forces full re-index
    else:
        console.print("   [green]✓ Configuration unchanged[/green]")
    
    # Step 4: Load manifest and determine what to index
    console.print("[dim]4. Analyzing files to index...[/dim]")
    manifest = load_manifest(state_dir)
    
    if not manifest:
        console.print("   [red]✗ Manifest is empty. Nothing to index.[/red]")
        return
    
    if force:
        files_to_index = manifest
        console.print(f"   [yellow]→ Full re-index: {len(files_to_index)} files[/yellow]")
    else:
        files_to_index = state_manager.get_files_to_index(manifest)
        
        if not files_to_index:
            console.print("   [green]✓ All files already indexed - nothing to do![/green]")
            console.print(f"\n[bold green]✅ Index is up to date![/bold green]")
            console.print(f"   • Total indexed files: {len(manifest)}")
            return
        
        console.print(f"   [cyan]→ Incremental index: {len(files_to_index)} files need updating[/cyan]")
    
    # Step 5: Ensure index directory exists
    console.print("[dim]5. Preparing index directory...[/dim]")
    index_dir = state_dir / "index"
    index_dir.mkdir(exist_ok=True)
    console.print(f"   [green]✓ Index directory ready[/green]")
    
    # Step 6: Display indexing summary
    console.print("\n[bold cyan]Indexing Summary:[/bold cyan]")
    console.print(f"  • Total tracked files: {len(manifest)}")
    console.print(f"  • Files to index: {len(files_to_index)}")
    console.print(f"  • Already indexed: {len(manifest) - len(files_to_index)}")
    console.print(f"  • Index mode: {'[yellow]Full re-index[/yellow]' if force else '[cyan]Incremental[/cyan]'}")
    console.print(f"  • Chunk size: {config['rag']['chunk_size']}")
    console.print(f"  • Vector store: {config['rag']['store']}")
    console.print()
    
    # Step 7: Perform the actual indexing (Timeline 3 - you'll implement this)
    console.print("[bold]Building embeddings...[/bold]")
    
    try:
        # This is where you'll add the actual embedding generation in Timeline 3
        # For now, we'll simulate it
        _build_embeddings(files_to_index, config, index_dir, state_manager)
        
        # Step 8: Update state after successful indexing
        state_manager.mark_files_indexed(files_to_index)
        state_manager.update_config_hash(current_config_hash)
        state_manager.update_index_time()
        state_manager.update_metadata(
            total_files=len(manifest),
            total_chunks=len(files_to_index) * 10  # Placeholder ## TODO change this later
        )
        
        console.print(f"\n[bold green]✅ Indexing complete![/bold green]")
        console.print(f"   • Indexed: {len(files_to_index)} files")
        console.print(f"   • Total in index: {len(manifest)} files")
        console.print(f"   • Index location: {index_dir}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Indexing failed:[/bold red] {e}")
        raise


def ensure_project_indexed(project_root: Path):
    """
    Ensures project is scanned and indexed. Used by analyze command.
    This is the auto-detection logic that makes analyze "just work".
    """
    state_dir = ensure_state_dir(project_root)
    state_manager = StateManager(state_dir)
    manifest_path = state_dir / "manifest.json"
    
    needs_scan = False
    needs_index = False
    
    # Check if scan is needed
    if not manifest_path.exists():
        needs_scan = True
        console.print("[yellow]⚠ Project not scanned. Running scan...[/yellow]")
    else:
        # Check if manifest is outdated (you could add more sophisticated checking)
        manifest = load_manifest(state_dir)
        if not manifest:
            needs_scan = True
            console.print("[yellow]⚠ Manifest is empty. Running scan...[/yellow]")
    
    # Run scan if needed
    if needs_scan:
        from bugtrace.analyze.core import analyze as scan_project
        scan_project(project_root)
        console.print()
    
    # Check if index is needed
    manifest = load_manifest(state_dir)
    
    # Check if index exists
    index_dir = state_dir / "index"
    if not index_dir.exists() or not any(index_dir.iterdir()):
        needs_index = True
        console.print("[yellow]⚠ No index found. Building index...[/yellow]\n")
    else:
        # Check if config changed
        config = load_user_config(project_root)
        current_config_hash = hash_config(config)
        
        if state_manager.config_changed(current_config_hash):
            needs_index = True
            console.print("[yellow]⚠ Configuration changed. Rebuilding index...[/yellow]\n")
        else:
            # Check if there are new/changed files
            files_to_index = state_manager.get_files_to_index(manifest)
            
            if files_to_index:
                needs_index = True
                console.print(f"[yellow]⚠ {len(files_to_index)} files changed. Updating index...[/yellow]\n")
    
    # Run index if needed
    if needs_index:
        index_project(project_root, force=False)
        console.print()
    else:
        console.print("[green]✓ Project index is up to date[/green]\n")


def _build_embeddings(
    files_to_index: Dict[str, str],
    config: dict,
    index_dir: Path,
    state_manager: StateManager
):
    """
    Build embeddings for files and store in vector database.
    
    Args:
        files_to_index: Dict of {filepath: hash} to index
        config: User configuration
        index_dir: Directory for vector store
        state_manager: State manager instance
    """

    from bugtrace.rag.embeddings import get_embedder
    from bugtrace.rag.chunker import Chunker
    from bugtrace.rag.vector_store import VectorStore
    from pathlib import Path as FilePath
    
    if not files_to_index:
        return

    # Initialize components
    console.print("[dim]Initializing embedding system...[/dim]")
    
    try:
        embedder = get_embedder(config)
        console.print(f"   [green]✓ Embedder ready (dimension: {embedder.get_dimension()})[/green]")
    except Exception as e:
        console.print(f"   [red]✗ Failed to initialize embedder: {e}[/red]")
        raise

    chunker = Chunker(
        chunk_size=config['rag']['chunk_size'],
        chunk_overlap=config['rag']['chunk_overlap']
    )

    # Get project root from first file path
    first_file = FilePath(list(files_to_index.keys())[0])
    project_root = first_file.parent
    while project_root.parent != project_root:
        if (project_root / ".bugtrace").exists():
            break
        project_root = project_root.parent
    
      # Initialize embedder
    embedder = get_embedder(config)
    
    vector_store = VectorStore(index_dir, project_root, embedder=embedder)
    console.print(f"   [green]✓ Vector store ready: {vector_store.collection_name}[/green]\n")
    

# Process files with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task(
            f"Processing {len(files_to_index)} files...",
            total=len(files_to_index)
        )
        
        total_chunks = 0
        
        for filepath_str in files_to_index.keys():
            filepath = FilePath(filepath_str)
            
            try:
                # Read file content
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                
                # Delete old chunks for this file
                vector_store.delete_file_chunks(str(filepath))
                
                # Chunk the file
                chunks = chunker.chunk_file(filepath, content)
                
                if not chunks:
                    progress.advance(task)
                    continue
                
                # Generate embeddings
                texts = [chunk['text'] for chunk in chunks]
                embeddings = embedder.embed_texts(texts)
                
                # Store in vector database
                vector_store.add_chunks(chunks, embeddings)
                
                total_chunks += len(chunks)
                progress.update(
                    task,
                    description=f"Processed {filepath.name}: {len(chunks)} chunks"
                )
                
            except Exception as e:
                console.print(f"   [yellow]⚠ Error processing {filepath.name}: {e}[/yellow]")
            
            progress.advance(task)
        
        progress.update(task, description=f"[green]✓ Completed: {total_chunks} chunks indexed")
    # Update state metadata with actual chunk count
    state_manager.update_metadata(total_chunks=total_chunks)
    