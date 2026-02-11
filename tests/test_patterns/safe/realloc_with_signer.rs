use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod safe_program {
    use super::*;

    pub fn resize_account(ctx: Context<ResizeAccount>) -> Result<()> {
        msg!("Account resized safely");
        Ok(())
    }
}

/// Payer is correctly typed as Signer<'info> — safe pattern.
#[derive(Accounts)]
pub struct ResizeAccount<'info> {
    #[account(
        mut,
        realloc = 200,
        realloc::payer = payer,
        realloc::zero = false,
    )]
    pub data_account: Account<'info, DataAccount>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[account]
pub struct DataAccount {
    pub data: Vec<u8>,
}
