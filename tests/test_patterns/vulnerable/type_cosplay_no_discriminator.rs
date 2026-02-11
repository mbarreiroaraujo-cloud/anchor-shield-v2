use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod vulnerable_program {
    use super::*;

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        // Deserializing from raw AccountInfo without type/owner check
        let data = ctx.accounts.vault_info.try_borrow_data()?;
        let balance = u64::from_le_bytes(data[40..48].try_into().unwrap());
        require!(amount <= balance, CustomError::InsufficientFunds);
        // Transfer logic...
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    /// Raw AccountInfo — no discriminator or owner check
    pub vault_info: AccountInfo<'info>,

    pub system_program: Program<'info, System>,
}

#[error_code]
pub enum CustomError {
    #[msg("Insufficient funds")]
    InsufficientFunds,
}
